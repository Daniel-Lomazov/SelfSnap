param(
    [string]$PythonExe = "",
    [switch]$RemoveUserData
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

function Get-ResolvedRepoRoot {
    param(
        [string]$RepoRoot
    )

    return (Resolve-Path $RepoRoot).Path
}

function Get-PreferredOneDriveRoot {
    if ($env:OneDrive) {
        return $env:OneDrive
    }
    return (Join-Path $env:USERPROFILE "OneDrive")
}

function Get-StorageTargetsFromConfig {
    param(
        [string]$ConfigPath
    )

    $defaultCaptureRoot = Join-Path $env:USERPROFILE "Pictures\SelfSnap\captures"
    $defaultArchiveRoot = Join-Path $env:USERPROFILE "Pictures\SelfSnap\archive"
    $oneDriveRoot = Get-PreferredOneDriveRoot
    $oneDriveCaptureRoot = Join-Path $oneDriveRoot "Pictures\SelfSnap\captures"
    $oneDriveArchiveRoot = Join-Path $oneDriveRoot "Pictures\SelfSnap\archive"

    $result = [ordered]@{
        capture_root = $defaultCaptureRoot
        archive_root = $defaultArchiveRoot
        owned_roots = @($defaultCaptureRoot, $defaultArchiveRoot, $oneDriveCaptureRoot, $oneDriveArchiveRoot)
    }

    if (-not (Test-Path $ConfigPath)) {
        return $result
    }

    try {
        $config = Get-Content -Path $ConfigPath -Raw | ConvertFrom-Json
    }
    catch {
        Write-Warning "Could not read config at $ConfigPath while resolving uninstall cleanup paths. Falling back to default roots."
        return $result
    }

    if ($config.capture_storage_root) {
        $result.capture_root = [string]$config.capture_storage_root
    }
    if ($config.archive_storage_root) {
        $result.archive_root = [string]$config.archive_storage_root
    }
    return $result
}

function Remove-ManagedCaptureFiles {
    param(
        [string]$RootPath
    )

    if (-not (Test-Path $RootPath)) {
        return
    }

    Get-ChildItem -Path $RootPath -Recurse -File -Filter "cap_*.png" -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue

    Get-ChildItem -Path $RootPath -Recurse -Directory -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        ForEach-Object {
            try {
                $_.Delete()
            }
            catch {
            }
        }

    try {
        Remove-Item -LiteralPath $RootPath -Force
    }
    catch {
        return
    }
}

function Remove-StorageRoot {
    param(
        [string]$RootPath,
        [string[]]$OwnedRoots
    )

    if (-not $RootPath) {
        return
    }

    try {
        $resolvedRoot = (Resolve-Path $RootPath).Path
    }
    catch {
        return
    }

    foreach ($ownedRoot in $OwnedRoots) {
        try {
            $resolvedOwnedRoot = (Resolve-Path $ownedRoot).Path
        }
        catch {
            continue
        }
        if ($resolvedOwnedRoot -eq $resolvedRoot) {
            Remove-Item -LiteralPath $resolvedRoot -Recurse -Force -ErrorAction SilentlyContinue
            return
        }
    }

    Remove-ManagedCaptureFiles -RootPath $resolvedRoot
}

function Get-TrustedInstallMetadata {
    param(
        [string]$MetaPath,
        [string]$RepoRoot
    )

    if (-not (Test-Path $MetaPath)) {
        return $null
    }

    try {
        $meta = Get-Content -Path $MetaPath -Raw | ConvertFrom-Json
    }
    catch {
        Write-Warning "Ignoring unreadable install metadata at $MetaPath."
        return $null
    }

    if (-not $meta.repo_root) {
        return $null
    }

    try {
        $metaRoot = (Resolve-Path $meta.repo_root).Path
    }
    catch {
        return $null
    }

    $resolvedRepoRoot = Get-ResolvedRepoRoot $RepoRoot
    if ($metaRoot -ne $resolvedRepoRoot) {
        return $null
    }

    return $meta
}

function Get-UninstallPythonCandidates {
    param(
        [string]$RepoRoot,
        [string]$MetaPath,
        [string]$ExplicitPythonExe
    )

    $candidates = New-Object System.Collections.Generic.List[string]

    if ($ExplicitPythonExe) {
        if (Test-Path $ExplicitPythonExe) {
            $candidates.Add((Resolve-Path $ExplicitPythonExe).Path)
        }
        else {
            $resolved = (& $ExplicitPythonExe -c "import sys; print(sys.executable)").Trim()
            Assert-LastExitCode "python override resolution"
            if ($resolved) {
                $candidates.Add($resolved)
            }
        }
    }
    $trustedMeta = Get-TrustedInstallMetadata -MetaPath $MetaPath -RepoRoot $RepoRoot

    $repoVenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $repoVenvPython) {
        $candidates.Add($repoVenvPython)
    }

    if ($trustedMeta -and $trustedMeta.python_executable -and (Test-Path $trustedMeta.python_executable)) {
        $candidates.Add($trustedMeta.python_executable)
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand -and $pythonCommand.Source) {
        $candidates.Add($pythonCommand.Source)
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand -and $pyCommand.Source) {
        foreach ($version in @("-3.12", "-3.11", "-3")) {
            try {
                $resolved = (& $pyCommand.Source $version -c "import sys; print(sys.executable)").Trim()
                if ($resolved) {
                    $candidates.Add($resolved)
                }
            }
            catch {
                continue
            }
        }
    }

    return $candidates | Select-Object -Unique
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$appRoot = Join-Path $env:LOCALAPPDATA "SelfSnap"
$binRoot = Join-Path $appRoot "bin"
$metaPath = Join-Path $binRoot "install-meta.json"
$configPath = Join-Path $appRoot "config\config.json"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = Join-Path $startupDir "SelfSnap Win11.lnk"
$picturesRoot = Join-Path $env:USERPROFILE "Pictures\SelfSnap"
$storageTargets = Get-StorageTargetsFromConfig -ConfigPath $configPath

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
foreach ($pythonCandidate in Get-UninstallPythonCandidates -RepoRoot $repoRoot -MetaPath $metaPath -ExplicitPythonExe $PythonExe) {
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

if ($RemoveUserData) {
    Remove-StorageRoot -RootPath $storageTargets.capture_root -OwnedRoots $storageTargets.owned_roots
    Remove-StorageRoot -RootPath $storageTargets.archive_root -OwnedRoots $storageTargets.owned_roots
    if (Test-Path $appRoot) {
        Remove-Item $appRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if (-not $packageRemoved) {
    Write-Warning "SelfSnap wrapper files were removed, but no installed selfsnap-win11 package was found in the checked Python environments."
}

Write-Host "SelfSnap startup shortcut, wrapper files, scheduled tasks, and editable package install were removed."
if ($RemoveUserData) {
    Write-Host "SelfSnap user data under $appRoot and managed screenshot/archive data were also removed."
}
else {
    Write-Host "Preserved app data under $appRoot and screenshots/archive under $picturesRoot."
}
