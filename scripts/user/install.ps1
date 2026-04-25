param(
    [string]$PythonExe = "",
    [string]$PythonwExe = ""
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$scriptHelpers = Join-Path $PSScriptRoot "..\shared\_selfsnap_script_helpers.ps1"
. $scriptHelpers

$repoRoot = Get-SelfSnapRepoRoot
$appRoot = Join-Path $env:LOCALAPPDATA "SelfSnap"
$binRoot = Join-Path $appRoot "bin"
$wrapperPath = Join-Path $binRoot "SelfSnap.cmd"
$metaPath = Join-Path $binRoot "install-meta.json"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = Join-Path $startupDir "SelfSnap Win11.lnk"

$pythonFullPath = Resolve-PythonPath -PythonPreference $PythonExe -RepoRoot $repoRoot
$pythonwPath = Resolve-PythonwPath -PythonPath $pythonFullPath -ExplicitPythonw $PythonwExe

function Get-InstalledSchemaSupport {
    param(
        [string]$PythonPath
    )

    $probeOutput = & $PythonPath -c "from selfsnap.models import SCHEMA_VERSION; from selfsnap.paths import resolve_app_paths; import json; print(json.dumps({'supported_schema_version': SCHEMA_VERSION, 'config_path': str(resolve_app_paths().config_path)}))"
    Assert-LastExitCode "schema support probe"
    return $probeOutput | ConvertFrom-Json
}

Push-Location $repoRoot

Write-Host "Installing SelfSnap from source for the current user..."

if (Test-PipAvailable $pythonFullPath) {
    & $pythonFullPath -m pip install -e $repoRoot
    Assert-LastExitCode "pip install"
}
else {
    $uvCommand = Get-UvCommand
    if (-not $uvCommand) {
        throw "uv was not found on PATH, and the selected Python environment does not provide pip."
    }
    & $uvCommand pip install --python $pythonFullPath -e $repoRoot
    Assert-LastExitCode "uv pip install"
}

New-Item -ItemType Directory -Path $binRoot -Force | Out-Null

$wrapperContent = @"
@echo off
setlocal
"$pythonFullPath" -m selfsnap %*
"@
Set-Content -Path $wrapperPath -Value $wrapperContent -Encoding Ascii

# Ensure the bin directory is on the user PATH
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$binRoot*") {
    $newPath = if ($userPath) { "$userPath;$binRoot" } else { $binRoot }
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    $env:PATH = "$env:PATH;$binRoot"
    Write-Host "Added $binRoot to user PATH."
}
else {
    Write-Host "$binRoot is already present on user PATH."
}

@{
    metadata_version = 1
    python_executable = $pythonFullPath
    pythonw_executable = $pythonwPath
    repo_root = $repoRoot
    installed_at_utc = [DateTime]::UtcNow.ToString("o")
} | ConvertTo-Json | Set-Content -Path $metaPath -Encoding UTF8

$schemaSupport = Get-InstalledSchemaSupport -PythonPath $pythonFullPath
$configPath = [string]$schemaSupport.config_path
$supportedSchemaVersion = [int]$schemaSupport.supported_schema_version
$skipConfigIntegration = $false

if (Test-Path $configPath) {
    try {
        $configPayload = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
        if ($null -ne $configPayload.schema_version) {
            $configSchemaVersion = [int]$configPayload.schema_version
            if ($configSchemaVersion -gt $supportedSchemaVersion) {
                $skipConfigIntegration = $true
                Write-Warning (
                    "Install completed, but this preview build supports config schema $supportedSchemaVersion while " +
                    "'$configPath' is schema $configSchemaVersion. Scheduler sync and startup shortcut updates were " +
                    "skipped to avoid rewriting a newer config with an older preview build."
                )
            }
        }
    }
    catch {
    }
}

if (-not $skipConfigIntegration) {
    & $wrapperPath sync-scheduler
    Assert-LastExitCode "scheduler sync"

    $startupEligibility = (& $pythonFullPath -c "from selfsnap.paths import resolve_app_paths; from selfsnap.config_store import load_or_create_config; config = load_or_create_config(resolve_app_paths()); print('true' if config.start_tray_on_login and config.first_run_completed else 'false')").Trim()
    Assert-LastExitCode "startup eligibility resolution"

    if ($startupEligibility -eq "true") {
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $pythonwPath
        $shortcut.Arguments = "-m selfsnap tray"
        $shortcut.WorkingDirectory = $repoRoot
        $shortcut.Save()
    } elseif (Test-Path $shortcutPath) {
        Remove-Item $shortcutPath -Force
    }
}

Pop-Location

Write-Host "SelfSnap source-based install completed for the current user."
Write-Host "Wrapper: $wrapperPath"
Write-Host "Startup shortcut: $shortcutPath"
