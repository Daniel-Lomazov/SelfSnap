param(
    [switch]$ListOnly,
    [switch]$Aggressive,
    [switch]$IncludeLocalAppData
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-ArtifactTargets {
    $targets = New-Object System.Collections.Generic.List[System.IO.FileSystemInfo]

    foreach ($literal in @(".pytest_cache", ".pytest_tmp", ".pytest-work")) {
        if (Test-Path -LiteralPath $literal) {
            $item = Get-Item -LiteralPath $literal -Force
            if ($item) {
                $targets.Add($item)
            }
        }
    }

    Get-ChildItem -Force -Directory -Filter "pytest-cache-files-*" | ForEach-Object {
        $targets.Add($_)
    }

    return $targets | Sort-Object FullName -Unique
}

function Get-LocalAppDataTargets {
    $localAppData = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME "AppData\\Local" }
    $pytestRoot = Join-Path $localAppData "SelfSnap\\pytest"
    if (Test-Path -LiteralPath $pytestRoot) {
        return @(Get-Item -LiteralPath $pytestRoot -Force)
    }
    return @()
}

function Remove-Artifact {
    param(
        [System.IO.FileSystemInfo]$Target,
        [switch]$UseAggressiveCleanup
    )

    try {
        Remove-Item -LiteralPath $Target.FullName -Recurse -Force -ErrorAction Stop
        return [pscustomobject]@{
            Path = $Target.FullName
            Removed = $true
            Method = "Remove-Item"
        }
    }
    catch {
        if (-not $UseAggressiveCleanup) {
            return [pscustomobject]@{
                Path = $Target.FullName
                Removed = $false
                Method = "Remove-Item"
                Error = $_.Exception.Message
            }
        }
    }

    $escaped = '"' + $Target.FullName + '"'
    if (-not (Test-Administrator)) {
        return [pscustomobject]@{
            Path = $Target.FullName
            Removed = $false
            Method = "takeown.exe+icacls.exe+rd"
            Error = "Aggressive cleanup requires an elevated PowerShell session."
        }
    }

    $cmd = "takeown.exe /f $escaped /r /d y && icacls.exe $escaped /grant:r %USERNAME%:(OI)(CI)F /t /c && rd /s /q $escaped"
    cmd /c $cmd | Out-Null
    if (-not (Test-Path -LiteralPath $Target.FullName)) {
        return [pscustomobject]@{
            Path = $Target.FullName
            Removed = $true
            Method = "takeown.exe+icacls.exe+rd"
        }
    }

    return [pscustomobject]@{
        Path = $Target.FullName
        Removed = $false
        Method = "takeown.exe+icacls.exe+rd"
        Error = "Target still exists after aggressive cleanup."
    }
}

$targets = Get-ArtifactTargets
if ($IncludeLocalAppData) {
    $targets += @(Get-LocalAppDataTargets)
    $targets = $targets | Sort-Object FullName -Unique
}
if (-not $targets) {
    Write-Host "No pytest artifact directories were found."
    exit 0
}

Write-Host "Pytest artifact targets:"
$targets | ForEach-Object {
    Write-Host " - $($_.FullName)"
}

if ($ListOnly) {
    exit 0
}

$results = foreach ($target in $targets) {
    Remove-Artifact -Target $target -UseAggressiveCleanup:$Aggressive
}

$failed = @($results | Where-Object { -not $_.Removed })
$results | ForEach-Object {
    if ($_.Removed) {
        Write-Host "Removed [$($_.Method)] $($_.Path)"
    }
    else {
        Write-Warning "Failed [$($_.Method)] $($_.Path): $($_.Error)"
    }
}

if ($failed.Count -gt 0) {
    Write-Warning "Some pytest artifact directories could not be removed."
    if (-not $Aggressive) {
        Write-Warning "Re-run with -Aggressive from an elevated PowerShell prompt if Windows ACLs are blocking deletion."
    }
    exit 1
}

Write-Host "Pytest artifact cleanup completed."
