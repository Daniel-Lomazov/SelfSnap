param(
    [string]$PythonPreference = "",
    [string]$VenvPath = ".venv",
    [switch]$NoDev
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$scriptHelpers = Join-Path $PSScriptRoot "..\shared\_selfsnap_script_helpers.ps1"
. $scriptHelpers

function Stop-LockingVenvToolProcesses {
    param(
        [string]$ScriptsPath
    )

    if (-not (Test-Path $ScriptsPath)) {
        return @()
    }

    $toolNames = @(
        "ruff.exe",
        "stubgen.exe",
        "stubtest.exe",
        "pip.exe",
        "pip3.exe",
        "pip3.11.exe",
        "pip3.12.exe",
        "virtualenv.exe",
        "wheel.exe"
    )

    $lockingProcesses = @(Get-Process -ErrorAction SilentlyContinue |
        Where-Object {
            try {
                $_.Path -and
                $_.Path.StartsWith($ScriptsPath, [System.StringComparison]::OrdinalIgnoreCase) -and
                ($toolNames -contains [System.IO.Path]::GetFileName($_.Path).ToLowerInvariant())
            }
            catch {
                $false
            }
        })

    foreach ($process in $lockingProcesses) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        Wait-Process -Id $process.Id -Timeout 5 -ErrorAction SilentlyContinue
    }

    return $lockingProcesses
}

$repoRoot = Get-SelfSnapRepoRoot
$venvFullPath = Join-Path $repoRoot $VenvPath
$venvScriptsPath = Join-Path $venvFullPath "Scripts"
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
    $stoppedToolProcesses = Stop-LockingVenvToolProcesses -ScriptsPath $venvScriptsPath
    if ($stoppedToolProcesses.Count -gt 0) {
        Write-Warning (
            "Stopped $($stoppedToolProcesses.Count) background tool process(es) from '$venvScriptsPath' to unlock setup."
        )
    }

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
            "Deactivate it and rerun scripts/user/setup.ps1, or pass -VenvPath to create a different environment."
        )
    }
}

Push-Location $repoRoot
try {
    if ($uvCommand -and $selectedPython) {
        $env:UV_CACHE_DIR = $uvCachePath
        $createArgs = @("venv", "--seed", "--python", $selectedPython)
        if (Test-Path $venvFullPath) {
            $createArgs += "--clear"
        }
        $createArgs += $VenvPath

        try {
            & $uvCommand @createArgs
            Assert-LastExitCode "uv venv creation"
        }
        catch {
            $scriptsPath = Join-Path $venvFullPath "Scripts"
            if (-not (Test-Path $scriptsPath)) {
                throw
            }

            Write-Warning (
                "uv could not clear '$venvFullPath' because files under '$scriptsPath' appear to be locked. " +
                "Retrying in place with --allow-existing."
            )

            $repairPython = Resolve-UvManagedPython -UvCommand $uvCommand
            if (-not $repairPython) {
                $repairPython = $selectedPython
            }

            $recoverySucceeded = $false
            for ($attempt = 1; $attempt -le 3; $attempt++) {
                try {
                    & $uvCommand venv --allow-existing --seed --python $repairPython $VenvPath
                    Assert-LastExitCode "uv venv in-place recovery"
                    $recoverySucceeded = $true
                    break
                }
                catch {
                    if ($attempt -lt 3) {
                        Write-Warning (
                            "In-place recovery attempt $attempt failed. Waiting briefly before retrying."
                        )
                        Start-Sleep -Milliseconds 500
                    }
                }
            }

            if (-not $recoverySucceeded) {
                throw (
                    "uv could not repair '$venvFullPath' in place after the clear step failed. Close any process " +
                    "using files under '$scriptsPath', or pass -VenvPath to create a different environment, " +
                    "then rerun scripts/user/setup.ps1."
                )
            }
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
    if (-not (Test-Path $venvPython)) {
        throw (
            "Expected '$venvPython' after environment creation, but it is missing. Close any process holding files " +
            "under '$venvFullPath\Scripts' and rerun scripts/user/setup.ps1, or pass -VenvPath to create a " +
            "different environment."
        )
    }

    $stoppedToolProcesses = Stop-LockingVenvToolProcesses -ScriptsPath $venvScriptsPath
    if ($stoppedToolProcesses.Count -gt 0) {
        Write-Warning (
            "Stopped $($stoppedToolProcesses.Count) background tool process(es) from '$venvScriptsPath' before package installation."
        )
    }

    $extras = if ($NoDev) { "" } else { "[dev]" }
    $devExtrasDeferred = $false
    if ($uvCommand) {
        & $uvCommand pip install --python $venvPython -U pip setuptools wheel
        Assert-LastExitCode "uv pip bootstrap"

        & $uvCommand pip install --python $venvPython -e "."
        Assert-LastExitCode "uv runtime install"

        if (-not $NoDev) {
            for ($attempt = 1; $attempt -le 3; $attempt++) {
                $stoppedToolProcesses = Stop-LockingVenvToolProcesses -ScriptsPath $venvScriptsPath
                if ($stoppedToolProcesses.Count -gt 0) {
                    Write-Warning (
                        "Stopped $($stoppedToolProcesses.Count) background tool process(es) from '$venvScriptsPath' " +
                        "before development extras attempt $attempt."
                    )
                }

                try {
                    & $uvCommand pip install --python $venvPython -e ".${extras}"
                    Assert-LastExitCode "uv dev install"
                    break
                }
                catch {
                    if ($attempt -lt 3) {
                        Write-Warning (
                            "Development extras install attempt $attempt failed because a tool executable under " +
                            "'$venvScriptsPath' appears to be locked. Retrying after stopping background tool " +
                            "processes."
                        )
                        Start-Sleep -Milliseconds 500
                        continue
                    }

                    $devExtrasDeferred = $true
                    Write-Warning (
                        "Runtime setup succeeded, but development extras could not be fully refreshed because a tool " +
                        "executable under '$venvScriptsPath' is still locked. Close editor tooling such as ruff.exe " +
                        "and rerun scripts/user/setup.ps1 if you need the full dev toolchain, or use -NoDev when " +
                        "you only need the runtime environment."
                    )
                }
            }
        }
    }
    else {
        & $venvPython -m pip install -U pip setuptools wheel
        Assert-LastExitCode "pip bootstrap"

        & $venvPython -m pip install -e ".${extras}"
        Assert-LastExitCode "project install"
    }

    & $venvPython -m selfsnap doctor
    Assert-LastExitCode "runtime dependency verification"
}
finally {
    Pop-Location
}

Write-Host "SelfSnap environment is ready."
Write-Host "Virtual environment: $venvFullPath"
Write-Host "Interpreter: $venvPython"
Write-Host "Activate with: $VenvPath\Scripts\Activate.ps1"
