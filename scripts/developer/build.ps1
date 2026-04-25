param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$scriptHelpers = Join-Path $PSScriptRoot "..\shared\_selfsnap_script_helpers.ps1"
. $scriptHelpers

$repoRoot = Get-SelfSnapRepoRoot
$pythonFullPath = Resolve-PythonPath -PythonPreference $PythonExe -RepoRoot $repoRoot
$workerEntry = Join-Path $repoRoot "src\selfsnap\worker_main.py"
$trayEntry = Join-Path $repoRoot "src\selfsnap\tray_main.py"
$pyinstallerRoot = Join-Path $repoRoot "build\pyinstaller"
$specRoot = Join-Path $pyinstallerRoot "specs"
$workerWorkRoot = Join-Path $pyinstallerRoot "worker"
$trayWorkRoot = Join-Path $pyinstallerRoot "tray"
$distRoot = Join-Path $repoRoot "dist"

New-Item -ItemType Directory -Path $specRoot -Force | Out-Null
New-Item -ItemType Directory -Path $workerWorkRoot -Force | Out-Null
New-Item -ItemType Directory -Path $trayWorkRoot -Force | Out-Null

Push-Location $repoRoot

Write-Host "Building SelfSnapWorker.exe..."
& $pythonFullPath -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name SelfSnapWorker `
    --specpath $specRoot `
    --workpath $workerWorkRoot `
    --distpath $distRoot `
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
    --specpath $specRoot `
    --workpath $trayWorkRoot `
    --distpath $distRoot `
    --paths src `
    --collect-submodules pystray `
    $trayEntry
Assert-LastExitCode "PyInstaller tray build"

Pop-Location

Write-Host "Build artifacts are ready under $distRoot"
