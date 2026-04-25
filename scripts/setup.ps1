param(
    [string]$PythonPreference = "",
    [string]$VenvPath = ".venv",
    [switch]$NoDev
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

function Get-UvCommand {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) {
        return $uv.Source
    }
    return $null
}

function Resolve-RequestedPython {
    param(
        [string]$Requested
    )

    if (-not $Requested) {
        return $null
    }

    $resolved = (& $Requested -c "import sys; print(sys.executable)").Trim()
    Assert-LastExitCode "python path resolution"

    if (-not $resolved) {
        throw "Could not resolve the requested Python executable."
    }

    return $resolved
}

function Resolve-UvManagedPython {
    param(
        [string]$UvCommand
    )

    if (-not $UvCommand) {
        return $null
    }

    foreach ($version in @("3.12", "3.11")) {
        $pythonPath = (& $UvCommand python find $version --offline 2>$null).Trim()
        if ($LASTEXITCODE -eq 0 -and $pythonPath) {
            return $pythonPath
        }
    }

    return $null
}

function Resolve-DefaultPython {
    $candidates = @(
        @("python"),
        @("python3"),
        @("py", "-3.12"),
        @("py", "-3.11"),
        @("py")
    )

    foreach ($candidate in $candidates) {
        $commandName = $candidate[0]
        if (-not (Get-Command $commandName -ErrorAction SilentlyContinue)) {
            continue
        }

        try {
            $candidateArgs = if ($candidate.Length -gt 1) { $candidate[1..($candidate.Length - 1)] } else { @() }
            $resolved = (& $commandName @candidateArgs -c "import sys; print(sys.executable)" 2>$null).Trim()
            if ($LASTEXITCODE -eq 0 -and $resolved) {
                return $resolved
            }
        }
        catch {
            continue
        }
    }

    return $null
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvFullPath = Join-Path $repoRoot.Path $VenvPath
$uvCachePath = Join-Path $repoRoot.Path ".uv-cache"
$uvCommand = Get-UvCommand
$selectedPython = Resolve-RequestedPython $PythonPreference

if (-not $selectedPython) {
    $selectedPython = Resolve-UvManagedPython $uvCommand
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
