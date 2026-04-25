$script:SelfSnapScriptsRoot = Split-Path -Parent $PSScriptRoot
$script:SelfSnapRepoRoot = (Resolve-Path (Join-Path $script:SelfSnapScriptsRoot "..")).Path

function Assert-LastExitCode {
    param(
        [string]$Step
    )

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

function Get-SelfSnapRepoRoot {
    return $script:SelfSnapRepoRoot
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

    if (Test-Path $Requested) {
        return (Resolve-Path $Requested).Path
    }

    try {
        $resolved = (& $Requested -c "import sys; print(sys.executable)").Trim()
    }
    catch {
        throw "Could not resolve the requested Python executable '$Requested'."
    }

    Assert-LastExitCode "python path resolution"

    if (-not $resolved) {
        throw "Could not resolve the requested Python executable '$Requested'."
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
        $pythonPath = (& $UvCommand python find $version --offline --managed-python 2>$null).Trim()
        if ($LASTEXITCODE -eq 0 -and $pythonPath) {
            return $pythonPath
        }
    }

    return $null
}

function Resolve-DefaultPython {
    $candidates = @(
        @{ Command = "python"; Args = @() },
        @{ Command = "python3"; Args = @() },
        @{ Command = "py"; Args = @("-3.12") },
        @{ Command = "py"; Args = @("-3.11") },
        @{ Command = "py"; Args = @("-3") }
    )

    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Command -ErrorAction SilentlyContinue)) {
            continue
        }

        try {
            $resolved = (& $candidate.Command @($candidate.Args) -c "import sys; print(sys.executable)" 2>$null).Trim()
        }
        catch {
            continue
        }

        if ($LASTEXITCODE -eq 0 -and $resolved) {
            return $resolved
        }
    }

    return $null
}

function Test-PipAvailable {
    param(
        [string]$PythonPath
    )

    $result = (& $PythonPath -c "import importlib.util; print('yes' if importlib.util.find_spec('pip') else 'no')").Trim()
    Assert-LastExitCode "pip availability probe"
    return $result -eq "yes"
}

function Resolve-PythonPath {
    param(
        [string]$PythonPreference,
        [string]$RepoRoot
    )

    $resolvedPreference = Resolve-RequestedPython -Requested $PythonPreference
    if ($resolvedPreference) {
        return $resolvedPreference
    }

    if ($RepoRoot) {
        $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
        if (Test-Path $venvPython) {
            Write-Host "Using repo .venv Python: $venvPython"
            return (Resolve-Path $venvPython).Path
        }
    }

    $resolvedDefault = Resolve-DefaultPython
    if ($resolvedDefault) {
        return $resolvedDefault
    }

    throw "Could not resolve a usable Python executable. Pass -PythonExe with a full path to the intended interpreter."
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

    $candidate = Join-Path (Split-Path -Parent $PythonPath) "pythonw.exe"
    if (Test-Path $candidate) {
        return (Resolve-Path $candidate).Path
    }

    $basePrefix = (& $PythonPath -c "import sys; print(sys.base_prefix)").Trim()
    if ($basePrefix) {
        $candidate = Join-Path $basePrefix "pythonw.exe"
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    $pythonwCommand = Get-Command pythonw -ErrorAction SilentlyContinue
    if ($pythonwCommand -and $pythonwCommand.Source -and (Test-Path $pythonwCommand.Source)) {
        $sourcePath = $pythonwCommand.Source
        if ([System.IO.Path]::GetFileName($sourcePath).ToLowerInvariant() -eq "pythonw.exe") {
            return $sourcePath
        }
    }

    throw "pythonw.exe was not found next to the selected Python interpreter. Pass -PythonwExe with an explicit pythonw path if your environment layout is nonstandard."
}

function Get-SelfSnapPowerShellExe {
    $command = Get-Command powershell.exe -ErrorAction SilentlyContinue
    if ($command -and $command.Source) {
        return $command.Source
    }

    return "powershell.exe"
}

function Invoke-SelfSnapPowerShellScript {
    param(
        [string]$ScriptPath,
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory = ""
    )

    $powershellExe = Get-SelfSnapPowerShellExe
    $commandArguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $ScriptPath
    )
    if ($ArgumentList.Count -gt 0) {
        $commandArguments += $ArgumentList
    }

    if ($WorkingDirectory) {
        Push-Location $WorkingDirectory
        try {
            & $powershellExe @commandArguments
        }
        finally {
            Pop-Location
        }
        return
    }

    & $powershellExe @commandArguments
}