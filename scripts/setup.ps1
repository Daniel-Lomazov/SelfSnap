param(
    [string]$PythonPreference = "",
    [string]$VenvPath = ".venv",
    [switch]$NoDev
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$scriptHelpers = Join-Path $PSScriptRoot "_selfsnap_script_helpers.ps1"
. $scriptHelpers

$repoRoot = Get-SelfSnapRepoRoot
$venvFullPath = Join-Path $repoRoot $VenvPath
$uvCachePath = Join-Path $repoRoot ".uv-cache"
$uvCommand = Get-UvCommand
$selectedPython = Resolve-RequestedPython -Requested $PythonPreference

if (-not $selectedPython) {
    $selectedPython = Resolve-UvManagedPython -UvCommand $uvCommand
}

if (-not $selectedPython) {
    $selectedPython = Resolve-DefaultPython
}

if (Test-Path $venvFullPath) {
    try {
        $activeVenv = if ($env:VIRTUAL_ENV) { [System.IO.Path]::GetFullPath($env:VIRTUAL_ENV) } else { "" }
        $targetVenv = [System.IO.Path]::GetFullPath($venvFullPath)
    }
    catch {
        $activeVenv = ""
        $targetVenv = ""
    }

    if ($activeVenv -and $targetVenv -and $activeVenv.TrimEnd('\\') -ieq $targetVenv.TrimEnd('\\')) {
        throw (
            "The target virtual environment '$venvFullPath' is currently active in this shell. " +
            "Deactivate it and rerun scripts/setup.ps1, or pass -VenvPath to create a different environment."
        )
    }
}

Push-Location $repoRoot

if ($uvCommand -and $selectedPython) {
    $env:UV_CACHE_DIR = $uvCachePath
    try {
        & $uvCommand venv --clear --seed --python $selectedPython $VenvPath
        Assert-LastExitCode "uv venv creation"
    }
    catch {
        $scriptsPath = Join-Path $venvFullPath "Scripts"
        if (Test-Path $scriptsPath) {
            throw (
                "uv could not recreate '$venvFullPath'. If another shell or process is using files under " +
                "'$scriptsPath', close it or pass -VenvPath to use a different environment, then rerun scripts/setup.ps1."
            )
        }
        throw
    }
}
elseif ($selectedPython) {
    if (Test-Path $venvFullPath) {
        Remove-Item -LiteralPath $venvFullPath -Recurse -Force
    }
    & $selectedPython -m venv $VenvPath
    Assert-LastExitCode "python venv creation"
}
else {
    throw "No usable Python interpreter was found. Install Python 3.12 or 3.11, or install uv and rerun this script."
}

$venvPython = Join-Path $venvFullPath "Scripts\python.exe"

& $venvPython -m pip install -U pip setuptools wheel
Assert-LastExitCode "pip bootstrap"

$extras = if ($NoDev) { "" } else { "[dev]" }
& $venvPython -m pip install -e ".${extras}"
Assert-LastExitCode "project install"

& $venvPython -m selfsnap doctor
Assert-LastExitCode "runtime dependency verification"

Pop-Location

Write-Host "SelfSnap environment is ready."
Write-Host "Virtual environment: $venvFullPath"
Write-Host "Interpreter: $venvPython"
Write-Host "Activate with: $VenvPath\Scripts\Activate.ps1"
