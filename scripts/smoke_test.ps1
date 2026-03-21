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

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$wrapperPath = Join-Path $env:LOCALAPPDATA "SelfSnap\bin\SelfSnap.cmd"

Push-Location $repoRoot

Write-Host "Installing source-based wrapper..."
& (Join-Path $PSScriptRoot "install.ps1") -PythonExe $PythonExe
Assert-LastExitCode "install"

Write-Host "Running diagnostics through wrapper..."
& $wrapperPath diag
Assert-LastExitCode "wrapper diag"

Write-Host "Running manual capture through wrapper..."
& $wrapperPath capture --trigger manual
Assert-LastExitCode "wrapper manual capture"

Pop-Location
