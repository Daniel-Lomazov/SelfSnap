$ErrorActionPreference = "Stop"

param(
    [string]$PythonExe = "python"
)

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot

Write-Host "Running diagnostics..."
& $PythonExe -m selfsnap diag

Write-Host "Running manual capture..."
& $PythonExe -m selfsnap capture --trigger manual

Pop-Location

