param(
    [string]$PythonExe = "",
    [string]$PythonwExe = "",
    [switch]$UpdateSource,
    [string]$TargetTag = "",
    [switch]$RelaunchTray
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

function Resolve-PythonPath {
    param(
        [string]$PythonPreference,
        [string]$RepoRoot
    )

    if ($PythonPreference) {
        if (Test-Path $PythonPreference) {
            return (Resolve-Path $PythonPreference).Path
        }
        $resolved = (& $PythonPreference -c "import sys; print(sys.executable)").Trim()
        Assert-LastExitCode "python path resolution"
        if ($resolved) {
            return $resolved
        }
    }

    # Prefer the repo .venv when no explicit preference is given
    if ($RepoRoot) {
        $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
        if (Test-Path $venvPython) {
            Write-Host "Using repo .venv Python: $venvPython"
            return (Resolve-Path $venvPython).Path
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand -and $pythonCommand.Source) {
        $resolved = (& $pythonCommand.Source -c "import sys; print(sys.executable)").Trim()
        Assert-LastExitCode "python path resolution"
        if ($resolved) {
            return $resolved
        }
    }

    throw "Could not resolve a usable Python executable. Pass -PythonExe with a full path to the intended interpreter."
}

function Resolve-PythonwPath {
    param(
        [string]$PythonPath,
        [string]$ExplicitPythonw
    )

    if ($ExplicitPythonw) {
        if (Test-Path $ExplicitPythonw) {
            return (Resolve-Path $ExplicitPythonw).Path
        }
        $resolved = (& $ExplicitPythonw -c "import sys; print(sys.executable)").Trim()
        Assert-LastExitCode "pythonw path resolution"
        if ($resolved -and [System.IO.Path]::GetFileName($resolved).ToLowerInvariant() -eq "pythonw.exe") {
            return $resolved
        }
        throw "Explicit -PythonwExe must resolve to pythonw.exe."
    }

    $candidate = Join-Path (Split-Path -Parent $PythonPath) "pythonw.exe"
    if (Test-Path $candidate) {
        return (Resolve-Path $candidate).Path
    }

    # For .venv, pythonw.exe lives in the base Python install, not the venv Scripts dir
    $basePrefix = (& $PythonPath -c "import sys; print(sys.base_prefix)").Trim()
    if ($basePrefix) {
        $candidate = Join-Path $basePrefix "pythonw.exe"
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    throw "pythonw.exe was not found next to the selected Python interpreter. Pass -PythonwExe explicitly if needed."
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
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
            # Fetch all tags from origin and hard-reset to the requested tag.
            # This works regardless of local uncommitted changes.
            & git -c credential.interactive=never fetch origin --tags
            Assert-LastExitCode "git fetch --tags"
            & git reset --hard "refs/tags/$TargetTag"
            Assert-LastExitCode "git reset --hard $TargetTag"
        } else {
            # Legacy fast-forward pull (requires a clean working tree).
            $statusOutput = (& git status --porcelain --untracked-files=normal).Trim()
            Assert-LastExitCode "git status"
            if ($statusOutput) {
                throw "Reinstall from source update requires a clean repo. Commit, stash, or discard local changes first."
            }
            & git -c credential.interactive=never pull --ff-only
            Assert-LastExitCode "git pull --ff-only"
        }
    }

    & powershell -ExecutionPolicy Bypass -File $installScript -PythonExe $pythonFullPath -PythonwExe $pythonwFullPath
    Assert-LastExitCode "SelfSnap install"

    if ($RelaunchTray) {
        Start-Process -FilePath $pythonwFullPath -ArgumentList '-m','selfsnap','tray' -WorkingDirectory $repoRoot.Path -WindowStyle Hidden
    }
}
catch {
    if ($RelaunchTray) {
        Start-Process -FilePath $pythonwFullPath -ArgumentList '-m','selfsnap','tray' -WorkingDirectory $repoRoot.Path -WindowStyle Hidden
    }
    throw
}
finally {
    Pop-Location
}

Write-Host "SelfSnap reinstall completed."
