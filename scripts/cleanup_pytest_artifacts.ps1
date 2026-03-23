param(
    [switch]$ListOnly,
    [Alias("Aggressive")][switch]$RepairAcl,
    [switch]$IncludeLocalAppData,
    [switch]$RelaunchedElevated
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-RepairArgumentList {
    $arguments = @(
        "-ExecutionPolicy", "Bypass",
        "-File", $PSCommandPath
    )
    if ($RepairAcl) {
        $arguments += "-RepairAcl"
    }
    if ($IncludeLocalAppData) {
        $arguments += "-IncludeLocalAppData"
    }
    if ($ListOnly) {
        $arguments += "-ListOnly"
    }
    $arguments += "-RelaunchedElevated"
    return $arguments
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

function Get-AllTargets {
    $targets = @(Get-ArtifactTargets)
    if ($IncludeLocalAppData) {
        $targets += @(Get-LocalAppDataTargets)
    }
    return @($targets | Sort-Object FullName -Unique)
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
                Error = "Normal removal failed. The target may be ACL-protected or still held open by a live process. Original error: $($_.Exception.Message)"
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

$targets = Get-AllTargets
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

if ($RepairAcl -and -not (Test-Administrator) -and -not $RelaunchedElevated) {
    Write-Host "Relaunching cleanup with elevation for ACL repair..."
    try {
        $process = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList (Get-RepairArgumentList) -Wait -PassThru
    }
    catch {
        Write-Warning "Elevation was not completed. Cleanup was not repaired."
        exit 2
    }

    $remainingTargets = Get-AllTargets
    if ($remainingTargets.Count -gt 0) {
        Write-Warning "Elevation returned, but pytest artifact targets still remain."
        Write-Warning "Either the UAC prompt was dismissed or the elevated cleanup did not complete successfully."
        $remainingTargets | ForEach-Object {
            Write-Warning "Remaining target: $($_.FullName)"
        }
        if ($process.ExitCode -ne 0) {
            exit $process.ExitCode
        }
        exit 3
    }

    exit $process.ExitCode
}

$results = foreach ($target in $targets) {
    Remove-Artifact -Target $target -UseAggressiveCleanup:$RepairAcl
}

$failed = @($results | Where-Object { -not $_.Removed })
$results | Format-Table Path, Removed, Method, Error -AutoSize | Out-String | Write-Host
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
    if (-not $RepairAcl) {
        Write-Warning "Re-run with -RepairAcl to attempt ownership repair and elevated cleanup."
        exit 1
    }
    exit 3
}

Write-Host "Pytest artifact cleanup completed."
