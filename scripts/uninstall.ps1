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

function Test-SelfSnapInstalled {
    param(
        [string]$PythonPath
    )

    if (-not (Test-PipAvailable $PythonPath)) {
        return $false
    }
    & $PythonPath -m pip show selfsnap-win11 *> $null
    return $LASTEXITCODE -eq 0
}

function Get-UninstallPythonCandidates {
    param(
        [string]$RepoRoot,
        [string]$MetaPath
    )

    $candidates = New-Object System.Collections.Generic.List[string]

    if (Test-Path $MetaPath) {
        $meta = Get-Content -Path $MetaPath -Raw | ConvertFrom-Json
        if ($meta.python_executable -and (Test-Path $meta.python_executable)) {
            $candidates.Add($meta.python_executable)
        }
    }

    $repoVenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $repoVenvPython) {
        $candidates.Add($repoVenvPython)
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand -and $pythonCommand.Source) {
        $candidates.Add($pythonCommand.Source)
    }

    return $candidates | Select-Object -Unique
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$appRoot = Join-Path $env:LOCALAPPDATA "SelfSnap"
$binRoot = Join-Path $appRoot "bin"
$metaPath = Join-Path $binRoot "install-meta.json"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = Join-Path $startupDir "SelfSnap Win11.lnk"
$picturesRoot = Join-Path $env:USERPROFILE "Pictures\SelfSnap"

if (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath -Force
}

$taskNames = schtasks /Query /FO CSV /NH 2>$null |
    ForEach-Object {
        if ($_ -match '^"([^"]+)"') { $matches[1] }
    } |
    Where-Object { $_ -like "\SelfSnap.Capture.*" }
Assert-LastExitCode "scheduled task query"

foreach ($taskName in $taskNames) {
    schtasks /Delete /TN ($taskName -replace '^\\', '') /F | Out-Null
    Assert-LastExitCode "scheduled task delete"
}

$packageRemoved = $false
foreach ($pythonCandidate in Get-UninstallPythonCandidates -RepoRoot $repoRoot -MetaPath $metaPath) {
    if (-not (Test-Path $pythonCandidate)) {
        continue
    }
    if (-not (Test-SelfSnapInstalled $pythonCandidate)) {
        continue
    }
    if (Test-PipAvailable $pythonCandidate) {
        & $pythonCandidate -m pip uninstall -y selfsnap-win11
        Assert-LastExitCode "package uninstall"
    }
    else {
        $uvCommand = Get-UvCommand
        & $uvCommand pip uninstall --python $pythonCandidate selfsnap-win11
        Assert-LastExitCode "uv package uninstall"
    }
    $packageRemoved = $true
    break
}

if (Test-Path $binRoot) {
    Remove-Item $binRoot -Recurse -Force
}

if (-not $packageRemoved) {
    Write-Warning "SelfSnap wrapper files were removed, but no installed selfsnap-win11 package was found in the checked Python environments."
}

Write-Host "SelfSnap startup shortcut, wrapper files, scheduled tasks, and editable package install were removed."
Write-Host "Preserved app data under $appRoot and screenshots/archive under $picturesRoot."
