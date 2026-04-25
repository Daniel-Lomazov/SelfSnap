param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$scriptHelpers = Join-Path $PSScriptRoot "_selfsnap_script_helpers.ps1"
. $scriptHelpers

$repoRoot = Get-SelfSnapRepoRoot
$pythonFullPath = Resolve-PythonPath -PythonPreference $PythonExe -RepoRoot $repoRoot
$workerEntry = Join-Path $repoRoot "src\selfsnap\worker_main.py"
$trayEntry = Join-Path $repoRoot "src\selfsnap\tray_main.py"
$distRoot = Join-Path $repoRoot "dist"

Push-Location $repoRoot

Write-Host "Building SelfSnapWorker.exe..."
& $pythonFullPath -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name SelfSnapWorker `
    --paths src `
    $workerEntry
Assert-LastExitCode "PyInstaller worker build"

Write-Host "Building SelfSnapTray.exe..."
& $pythonFullPath -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name SelfSnapTray `
    --paths src `
    --collect-submodules pystray `
    $trayEntry
Assert-LastExitCode "PyInstaller tray build"

Pop-Location

Write-Host "Build artifacts are ready under $distRoot"
