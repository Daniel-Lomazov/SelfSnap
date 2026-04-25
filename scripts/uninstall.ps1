param(
    [string]$PythonExe = "",
    [switch]$RemoveUserData
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$scriptHelpers = Join-Path $PSScriptRoot "_selfsnap_script_helpers.ps1"
. $scriptHelpers

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

    if ($metaRoot -ne $RepoRoot) {
        return $null
    }

    return $meta
}

function Test-IsSelfSnapTrayProcess {
    param(
        $Process,
        [string]$RepoRoot,
        [string]$PythonPath,
        [string]$PythonwPath
    )

    if (-not $Process) {
        return $false
    }

    $name = [string]$Process.Name
    $commandLine = [string]$Process.CommandLine
    if (-not $commandLine) {
        return $false
    }

    $isTrayCommand = (
        $commandLine -match '(?i)(?:^|\s)-m\s+selfsnap\s+tray(?:\s|$)'
    ) -or (
        $commandLine -match '(?i)\bselfsnap(?:\.cmd|\.exe)?\b.*\btray\b'
    )
    if (-not $isTrayCommand) {
        return $false
    }

    if ($RepoRoot -and $commandLine -like "*$RepoRoot*") {
        return $true
    }
    if ($PythonPath -and $commandLine -like "*$PythonPath*") {
        return $true
    }
    if ($PythonwPath -and $commandLine -like "*$PythonwPath*") {
        return $true
    }

    return $name -match '^(?i)(python|pythonw|selfsnap)(\.exe)?$'
}

function Get-InvokingTrayProcessId {
    param(
        [string]$RepoRoot,
        [string]$PythonPath,
        [string]$PythonwPath
    )

    try {
        $scriptProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $PID"
    }
    catch {
        return $null
    }

    if (-not $scriptProcess -or -not $scriptProcess.ParentProcessId) {
        return $null
    }

    try {
        $parentProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($scriptProcess.ParentProcessId)"
    }
    catch {
        return $null
    }

    if (Test-IsSelfSnapTrayProcess -Process $parentProcess -RepoRoot $RepoRoot -PythonPath $PythonPath -PythonwPath $PythonwPath) {
        return [int]$parentProcess.ProcessId
    }

    return $null
}

function Stop-RunningSelfSnapTray {
    param(
        [string]$RepoRoot,
        [string]$PythonPath,
        [string]$PythonwPath,
        [int[]]$ExcludeProcessIds = @()
    )

    $trayProcesses = Get-CimInstance Win32_Process |
        Where-Object {
            $_.ProcessId -notin $ExcludeProcessIds -and
            (Test-IsSelfSnapTrayProcess -Process $_ -RepoRoot $RepoRoot -PythonPath $PythonPath -PythonwPath $PythonwPath)
        }

    foreach ($process in $trayProcesses) {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
        Wait-Process -Id $process.ProcessId -Timeout 5 -ErrorAction SilentlyContinue
    }

    return @($trayProcesses).Count
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

$repoRoot = Get-SelfSnapRepoRoot
$appRoot = Join-Path $env:LOCALAPPDATA "SelfSnap"
$binRoot = Join-Path $appRoot "bin"
$metaPath = Join-Path $binRoot "install-meta.json"
$configPath = Join-Path $appRoot "config\config.json"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = Join-Path $startupDir "SelfSnap Win11.lnk"
$picturesRoot = Join-Path $env:USERPROFILE "Pictures\SelfSnap"
$storageTargets = Get-StorageTargetsFromConfig -ConfigPath $configPath
$trustedMeta = Get-TrustedInstallMetadata -MetaPath $metaPath -RepoRoot $repoRoot
$knownPythonExe = if ($trustedMeta -and $trustedMeta.python_executable) {
    [string]$trustedMeta.python_executable
}
else {
    ""
}
$knownPythonwExe = if ($trustedMeta -and $trustedMeta.pythonw_executable) {
    [string]$trustedMeta.pythonw_executable
}
else {
    ""
}
$invokingTrayPid = Get-InvokingTrayProcessId -RepoRoot $repoRoot -PythonPath $knownPythonExe -PythonwPath $knownPythonwExe
$stoppedTrayCount = Stop-RunningSelfSnapTray -RepoRoot $repoRoot -PythonPath $knownPythonExe -PythonwPath $knownPythonwExe -ExcludeProcessIds @($invokingTrayPid)
if ($stoppedTrayCount -gt 0) {
    Write-Host "Stopped $stoppedTrayCount running SelfSnap tray process(es)."
}

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
        if (-not $uvCommand) {
            throw "uv was not found on PATH, and the selected Python environment does not provide pip."
        }
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
