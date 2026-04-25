param(
    [string]$PythonExe = "",
    [string]$PythonwExe = "",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$scriptHelpers = Join-Path $PSScriptRoot "..\shared\_selfsnap_script_helpers.ps1"
. $scriptHelpers

$repoRoot = Get-SelfSnapRepoRoot
$pythonFullPath = Resolve-PythonPath -PythonPreference $PythonExe -RepoRoot $repoRoot
$wrapperPath = Join-Path $env:LOCALAPPDATA "SelfSnap\bin\SelfSnap.cmd"

Push-Location $repoRoot

if (-not $SkipInstall) {
    $installArgs = @("-PythonExe", $pythonFullPath)
    if ($PythonwExe) {
        $pythonwFullPath = Resolve-PythonwPath -PythonPath $pythonFullPath -ExplicitPythonw $PythonwExe
        $installArgs += @("-PythonwExe", $pythonwFullPath)
    }

    Write-Host "Installing source-based wrapper..."
    Invoke-SelfSnapPowerShellScript -ScriptPath (Join-Path $repoRoot "scripts\user\install.ps1") -ArgumentList $installArgs -WorkingDirectory $repoRoot
    Assert-LastExitCode "install"
}
elseif (-not (Test-Path $wrapperPath)) {
    throw "Wrapper not found at $wrapperPath. Run scripts/user/install.ps1 first or omit -SkipInstall."
}

Write-Host "Running diagnostics through wrapper..."
& $wrapperPath diag
Assert-LastExitCode "wrapper diag"

Write-Host "Running manual capture through wrapper..."
& $wrapperPath capture --trigger manual
Assert-LastExitCode "wrapper manual capture"

Pop-Location
