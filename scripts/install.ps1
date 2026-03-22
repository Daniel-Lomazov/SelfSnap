param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

function Assert-LastExitCode {
    param(
        [string]$Step
    )

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

function Get-UvCommand {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) {
        return $uv.Source
    }
    throw "uv was not found on PATH, and the selected Python environment does not provide pip."
}

function Test-PipAvailable {
    param(
        [string]$PythonPath
    )

    $result = (& $PythonPath -c "import importlib.util; print('yes' if importlib.util.find_spec('pip') else 'no')").Trim()
    Assert-LastExitCode "pip availability probe"
    return $result -eq "yes"
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$appRoot = Join-Path $env:LOCALAPPDATA "SelfSnap"
$binRoot = Join-Path $appRoot "bin"
$wrapperPath = Join-Path $binRoot "SelfSnap.cmd"
$metaPath = Join-Path $binRoot "install-meta.json"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = Join-Path $startupDir "SelfSnap Win11.lnk"

$pythonFullPath = (& $PythonExe -c "import sys; print(sys.executable)").Trim()
Assert-LastExitCode "python path resolution"
if (-not $pythonFullPath) {
    throw "Could not resolve the full Python executable path."
}
$pythonwPath = Join-Path (Split-Path -Parent $pythonFullPath) "pythonw.exe"
if (-not (Test-Path $pythonwPath)) {
    throw "pythonw.exe was not found next to the selected Python interpreter. Background SelfSnap launch requires pythonw.exe."
}

Push-Location $repoRoot

if (Test-PipAvailable $pythonFullPath) {
    & $pythonFullPath -m pip install -e $repoRoot
    Assert-LastExitCode "pip install"
}
else {
    $uvCommand = Get-UvCommand
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

@{
    python_executable = $pythonFullPath
    pythonw_executable = $pythonwPath
    repo_root = $repoRoot.Path
    installed_at_utc = [DateTime]::UtcNow.ToString("o")
} | ConvertTo-Json | Set-Content -Path $metaPath -Encoding UTF8

& $wrapperPath sync-scheduler
Assert-LastExitCode "scheduler sync"

$startupEligibility = (& $pythonFullPath -c "from selfsnap.paths import resolve_app_paths; from selfsnap.config_store import load_or_create_config; config = load_or_create_config(resolve_app_paths()); print('true' if config.start_tray_on_login and config.first_run_completed else 'false')").Trim()
Assert-LastExitCode "startup eligibility resolution"

if ($startupEligibility -eq "true") {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $pythonwPath
    $shortcut.Arguments = "-m selfsnap tray"
    $shortcut.WorkingDirectory = $repoRoot.Path
    $shortcut.Save()
} elseif (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath -Force
}

Pop-Location

Write-Host "SelfSnap source-based install completed for the current user."
Write-Host "Wrapper: $wrapperPath"
Write-Host "Startup shortcut: $shortcutPath"
