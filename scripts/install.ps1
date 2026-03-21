$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$distRoot = Join-Path $repoRoot "dist"
$workerExe = Join-Path $distRoot "SelfSnapWorker.exe"
$trayExe = Join-Path $distRoot "SelfSnapTray.exe"

if (-not (Test-Path $workerExe) -or -not (Test-Path $trayExe)) {
    throw "Built executables were not found. Run scripts/build.ps1 first."
}

$appRoot = Join-Path $env:LOCALAPPDATA "SelfSnap"
$binRoot = Join-Path $appRoot "bin"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = Join-Path $startupDir "SelfSnap Win11.lnk"

New-Item -ItemType Directory -Path $binRoot -Force | Out-Null
Copy-Item $workerExe (Join-Path $binRoot "SelfSnapWorker.exe") -Force
Copy-Item $trayExe (Join-Path $binRoot "SelfSnapTray.exe") -Force

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $binRoot "SelfSnapTray.exe"
$shortcut.WorkingDirectory = $binRoot
$shortcut.Save()

& (Join-Path $binRoot "SelfSnapWorker.exe") sync-scheduler

Write-Host "SelfSnap installed for the current user."
Write-Host "Tray executable: $(Join-Path $binRoot 'SelfSnapTray.exe')"

