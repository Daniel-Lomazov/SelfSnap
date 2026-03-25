param(
    [string]$PythonExe = "python",
    [string]$PythonwExe = ""
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
    throw "uv was not found on PATH, and the selected Python environment does not provide pip."
}

function Test-PipAvailable {
    param(
        [string]$PythonPath
    )

    $result = (& $PythonPath -c "import importlib.util; print('yes' if importlib.util.find_spec('pip') else 'no')").Trim()
    Assert-LastExitCode "pip availability probe"
    return $result -eq "yes"
}

function Resolve-PythonwPath {
    param(
        [string]$PythonPath,
        [string]$ExplicitPythonw
    )

    if ($ExplicitPythonw) {
        $candidate = $null
        $pythonwCommand = Get-Command $ExplicitPythonw -ErrorAction SilentlyContinue
        if ($pythonwCommand -and $pythonwCommand.Source) {
            $candidate = $pythonwCommand.Source
        }
        elseif (Test-Path $ExplicitPythonw) {
            $candidate = (Resolve-Path $ExplicitPythonw).Path
        }
        if (-not $candidate) {
            throw "Explicit pythonw executable '$ExplicitPythonw' was not found. Pass a full path or a command available on PATH."
        }
        if ([System.IO.Path]::GetFileName($candidate).ToLowerInvariant() -ne "pythonw.exe") {
            throw "The explicit -PythonwExe value must resolve to pythonw.exe, got: $candidate"
        }
        return $candidate
    }

    # Same directory as python.exe (standard layout)
    $candidate = Join-Path (Split-Path -Parent $PythonPath) "pythonw.exe"
    if (Test-Path $candidate) {
        return (Resolve-Path $candidate).Path
    }

    # For .venv, pythonw.exe lives in the base Python install (e.g. uv-managed or system)
    $basePrefix = (& $PythonPath -c "import sys; print(sys.base_prefix)").Trim()
    if ($basePrefix) {
        $candidate = Join-Path $basePrefix "pythonw.exe"
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    $pythonwCommand = Get-Command pythonw -ErrorAction SilentlyContinue
    if ($pythonwCommand -and $pythonwCommand.Source -and (Test-Path $pythonwCommand.Source)) {
        $src = $pythonwCommand.Source
        if ([System.IO.Path]::GetFileName($src).ToLowerInvariant() -eq "pythonw.exe") {
            return $src
        }
    }

    throw "pythonw.exe was not found next to the selected Python interpreter. Pass -PythonwExe with an explicit pythonw path if your environment layout is nonstandard."
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

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand -and $pyCommand.Source) {
        $resolved = (& $pyCommand.Source -3 -c "import sys; print(sys.executable)").Trim()
        Assert-LastExitCode "py launcher path resolution"
        if ($resolved) {
            return $resolved
        }
    }

    throw "Could not resolve a usable Python executable. Pass -PythonExe with a full path to the intended interpreter."
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$appRoot = Join-Path $env:LOCALAPPDATA "SelfSnap"
$binRoot = Join-Path $appRoot "bin"
$wrapperPath = Join-Path $binRoot "SelfSnap.cmd"
$metaPath = Join-Path $binRoot "install-meta.json"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = Join-Path $startupDir "SelfSnap Win11.lnk"

$pythonFullPath = Resolve-PythonPath -PythonPreference $PythonExe -RepoRoot $repoRoot
$pythonwPath = Resolve-PythonwPath -PythonPath $pythonFullPath -ExplicitPythonw $PythonwExe

Push-Location $repoRoot

if (Test-PipAvailable $pythonFullPath) {
    & $pythonFullPath -m pip install -e $repoRoot
    Assert-LastExitCode "pip install"
}
else {
    $uvCommand = Get-UvCommand
    & $uvCommand pip install --python $pythonFullPath -e $repoRoot
    Assert-LastExitCode "uv pip install"
}

New-Item -ItemType Directory -Path $binRoot -Force | Out-Null

$wrapperContent = @"
@echo off
setlocal
"$pythonFullPath" -m selfsnap %*
"@
Set-Content -Path $wrapperPath -Value $wrapperContent -Encoding Ascii

# Ensure the bin directory is on the user PATH
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$binRoot*") {
    $newPath = if ($userPath) { "$userPath;$binRoot" } else { $binRoot }
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    $env:PATH = "$env:PATH;$binRoot"
    Write-Host "Added $binRoot to user PATH."
}

@{
    metadata_version = 1
    python_executable = $pythonFullPath
    pythonw_executable = $pythonwPath
    repo_root = $repoRoot.Path
    installed_at_utc = [DateTime]::UtcNow.ToString("o")
} | ConvertTo-Json | Set-Content -Path $metaPath -Encoding UTF8

& $wrapperPath sync-scheduler
Assert-LastExitCode "scheduler sync"

$startupEligibility = (& $pythonFullPath -c "from selfsnap.paths import resolve_app_paths; from selfsnap.config_store import load_or_create_config; config = load_or_create_config(resolve_app_paths()); print('true' if config.start_tray_on_login and config.first_run_completed else 'false')").Trim()
Assert-LastExitCode "startup eligibility resolution"

if ($startupEligibility -eq "true") {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $pythonwPath
    $shortcut.Arguments = "-m selfsnap tray"
    $shortcut.WorkingDirectory = $repoRoot.Path
    $shortcut.Save()
} elseif (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath -Force
}

Pop-Location

Write-Host "SelfSnap source-based install completed for the current user."
Write-Host "Wrapper: $wrapperPath"
Write-Host "Startup shortcut: $shortcutPath"
