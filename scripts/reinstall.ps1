param(
    [string]$PythonExe = "",
    [string]$PythonwExe = "",
    [switch]$UpdateSource,
    [string]$TargetTag = "",
    [switch]$RelaunchTray
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$scriptHelpers = Join-Path $PSScriptRoot "_selfsnap_script_helpers.ps1"
. $scriptHelpers

$repoRoot = Get-SelfSnapRepoRoot
$installScript = Join-Path $repoRoot "scripts\install.ps1"
$pythonFullPath = Resolve-PythonPath -PythonPreference $PythonExe -RepoRoot $repoRoot
$pythonwFullPath = Resolve-PythonwPath -PythonPath $pythonFullPath -ExplicitPythonw $PythonwExe

Push-Location $repoRoot
try {
    if ($UpdateSource) {
        if (-not (Test-Path (Join-Path $repoRoot ".git"))) {
            throw "Reinstall from source update requires a valid Git checkout with a .git directory."
        }

        $env:GIT_TERMINAL_PROMPT = "0"

        if ($TargetTag) {
            Write-Host "Updating source checkout to tag $TargetTag..."
            & git -c credential.interactive=never fetch origin --tags
            Assert-LastExitCode "git fetch --tags"
            & git reset --hard "refs/tags/$TargetTag"
            Assert-LastExitCode "git reset --hard $TargetTag"
        } else {
            Write-Host "Refreshing source checkout with git pull --ff-only..."
            $statusOutput = (& git status --porcelain --untracked-files=normal).Trim()
            Assert-LastExitCode "git status"
            if ($statusOutput) {
                throw "Reinstall from source update requires a clean repo. Commit, stash, or discard local changes first."
            }
            & git -c credential.interactive=never pull --ff-only
            Assert-LastExitCode "git pull --ff-only"
        }
    }

    Write-Host "Running source install..."
    Invoke-SelfSnapPowerShellScript -ScriptPath $installScript -ArgumentList @("-PythonExe", $pythonFullPath, "-PythonwExe", $pythonwFullPath) -WorkingDirectory $repoRoot
    Assert-LastExitCode "SelfSnap install"

    if ($RelaunchTray) {
        Write-Host "Relaunching tray..."
        Start-Process -FilePath $pythonwFullPath -ArgumentList '-m','selfsnap','tray' -WorkingDirectory $repoRoot -WindowStyle Hidden
    }
}
catch {
    if ($RelaunchTray) {
        Start-Process -FilePath $pythonwFullPath -ArgumentList '-m','selfsnap','tray' -WorkingDirectory $repoRoot -WindowStyle Hidden
    }
    throw
}
finally {
    Pop-Location
}

Write-Host "SelfSnap reinstall completed."
