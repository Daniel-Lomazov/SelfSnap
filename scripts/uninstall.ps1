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

$appRoot = Join-Path $env:LOCALAPPDATA "SelfSnap"
$binRoot = Join-Path $appRoot "bin"
$metaPath = Join-Path $binRoot "install-meta.json"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = Join-Path $startupDir "SelfSnap Win11.lnk"
$picturesRoot = Join-Path $env:USERPROFILE "Pictures\SelfSnap"

if (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath -Force
}

$taskNames = schtasks /Query /FO CSV /NH 2>$null |
    ForEach-Object {
        if ($_ -match '^"([^"]+)"') { $matches[1] }
    } |
    Where-Object { $_ -like "\SelfSnap.Capture.*" }
Assert-LastExitCode "scheduled task query"

foreach ($taskName in $taskNames) {
    schtasks /Delete /TN ($taskName -replace '^\\', '') /F | Out-Null
    Assert-LastExitCode "scheduled task delete"
}

if (Test-Path $metaPath) {
    $meta = Get-Content -Path $metaPath -Raw | ConvertFrom-Json
    if ($meta.python_executable -and (Test-Path $meta.python_executable)) {
        if (Test-PipAvailable $meta.python_executable) {
            & $meta.python_executable -m pip uninstall -y selfsnap-win11
            Assert-LastExitCode "package uninstall"
        }
        else {
            $uvCommand = Get-UvCommand
            & $uvCommand pip uninstall --python $meta.python_executable selfsnap-win11
            Assert-LastExitCode "uv package uninstall"
        }
    }
}

if (Test-Path $binRoot) {
    Remove-Item $binRoot -Recurse -Force
}

Write-Host "SelfSnap startup shortcut, wrapper files, scheduled tasks, and editable package install were removed."
Write-Host "Preserved app data under $appRoot and screenshots/archive under $picturesRoot."
