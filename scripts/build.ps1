$ErrorActionPreference = "Stop"

param(
    [string]$PythonExe = "python"
)

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot

& $PythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name SelfSnapWorker `
    --paths src `
    src/selfsnap/worker_main.py

& $PythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name SelfSnapTray `
    --paths src `
    --collect-submodules pystray `
    src/selfsnap/tray_main.py

Pop-Location
