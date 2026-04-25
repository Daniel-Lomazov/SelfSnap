param(
    [string]$PythonExe = "",
    [string]$Version = "",
    [string]$BuildLabel = "",
    [string]$ArtifactRoot = ""
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$scriptHelpers = Join-Path $PSScriptRoot "..\shared\_selfsnap_script_helpers.ps1"
. $scriptHelpers

function Get-PackageVersion {
    param(
        [string]$RepoRoot,
        [string]$RequestedVersion
    )

    if (-not [string]::IsNullOrWhiteSpace($RequestedVersion)) {
        $normalized = $RequestedVersion.Trim()
        if ($normalized.StartsWith("v")) {
            $normalized = $normalized.Substring(1)
        }
    }
    else {
        $pyprojectPath = Join-Path $RepoRoot "pyproject.toml"
        $versionLine = Select-String -Path $pyprojectPath -Pattern '^version = "([^"]+)"$' | Select-Object -First 1
        if (-not $versionLine) {
            throw "Could not resolve the project version from $pyprojectPath."
        }
        $normalized = $versionLine.Matches[0].Groups[1].Value
    }

    if ($normalized -notmatch '^\d+\.\d+\.\d+$') {
        throw "Packaging currently expects a three-part semantic version, got '$normalized'."
    }

    return $normalized
}

function Get-SanitizedBuildLabel {
    param(
        [string]$RawLabel
    )

    if ([string]::IsNullOrWhiteSpace($RawLabel)) {
        return ""
    }

    $sanitized = ($RawLabel.Trim().ToLowerInvariant() -replace '[^a-z0-9.-]+', '-').Trim('-')
    if (-not $sanitized) {
        return ""
    }

    return "-$sanitized"
}

function Initialize-CleanDirectory {
    param(
        [string]$Path
    )

    if (Test-Path $Path) {
        Remove-Item -Path $Path -Recurse -Force
    }

    New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

function Expand-ZipToDirectory {
    param(
        [string]$ZipPath,
        [string]$DestinationDirectory
    )

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    if (Test-Path $DestinationDirectory) {
        Remove-Item -Path $DestinationDirectory -Recurse -Force
    }

    [System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, $DestinationDirectory)
}

function Get-WixToolset {
    $candleCommand = Get-Command candle.exe -ErrorAction SilentlyContinue
    $lightCommand = Get-Command light.exe -ErrorAction SilentlyContinue
    if ($candleCommand -and $lightCommand) {
        return @{
            Candle = $candleCommand.Source
            Light = $lightCommand.Source
        }
    }

    $downloadRoot = Join-Path $env:TEMP "selfsnap-wix314"
    $zipPath = Join-Path $downloadRoot "wix314-binaries.zip"
    $extractRoot = Join-Path $downloadRoot "wix314-binaries"
    $candlePath = Join-Path $extractRoot "candle.exe"
    $lightPath = Join-Path $extractRoot "light.exe"

    if (-not ((Test-Path $candlePath) -and (Test-Path $lightPath))) {
        New-Item -ItemType Directory -Path $downloadRoot -Force | Out-Null
        Write-Host "Downloading WiX build tools..."
        Invoke-WebRequest -Uri "https://github.com/wixtoolset/wix3/releases/download/wix3141rtm/wix314-binaries.zip" -OutFile $zipPath
        Expand-ZipToDirectory -ZipPath $zipPath -DestinationDirectory $extractRoot
    }

    if (-not ((Test-Path $candlePath) -and (Test-Path $lightPath))) {
        throw "WiX build tools could not be downloaded or extracted into $extractRoot."
    }

    return @{
        Candle = $candlePath
        Light = $lightPath
    }
}

function Write-PortableReadme {
    param(
        [string]$Version,
        [string]$BuildLabel,
        [string]$OutputPath
    )

    $lines = @(
        "SelfSnap Windows portable package",
        "",
        "Version: $Version",
        $(if ($BuildLabel) { "Build label: $BuildLabel" } else { $null }),
        "",
        "Contents:",
        "- SelfSnapTray.exe launches the windowless tray application.",
        "- SelfSnapWorker.exe provides the CLI and worker entrypoint.",
        "",
        "Notes:",
        "- Config, logs, and capture metadata are still stored under %LOCALAPPDATA%\SelfSnap.",
        "- The portable build is intended for direct launch or smoke validation of the compiled EXEs.",
        "- For a standard Windows install/uninstall surface, prefer the MSI or setup EXE generated beside this package."
    ) | Where-Object { $null -ne $_ }

    Set-Content -Path $OutputPath -Value $lines -Encoding Ascii
}

function New-ZipFromDirectory {
    param(
        [string]$SourceDirectory,
        [string]$DestinationPath
    )

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    if (Test-Path $DestinationPath) {
        Remove-Item -Path $DestinationPath -Force
    }

    [System.IO.Compression.ZipFile]::CreateFromDirectory(
        $SourceDirectory,
        $DestinationPath,
        [System.IO.Compression.CompressionLevel]::Optimal,
        $false
    )
}

$repoRoot = Get-SelfSnapRepoRoot
$pythonFullPath = Resolve-PythonPath -PythonPreference $PythonExe -RepoRoot $repoRoot
$packageVersion = Get-PackageVersion -RepoRoot $repoRoot -RequestedVersion $Version
$artifactSuffix = Get-SanitizedBuildLabel -RawLabel $BuildLabel
$artifactRootPath = if ([string]::IsNullOrWhiteSpace($ArtifactRoot)) {
    Join-Path $repoRoot "artifacts\windows"
}
elseif ([System.IO.Path]::IsPathRooted($ArtifactRoot)) {
    $ArtifactRoot
}
else {
    Join-Path $repoRoot $ArtifactRoot
}

$stageRoot = Join-Path $artifactRootPath "stage"
$portableRoot = Join-Path $artifactRootPath "portable"
$wixWorkRoot = Join-Path $artifactRootPath "wix"
$distRoot = Join-Path $repoRoot "dist"
$buildScript = Join-Path $repoRoot "scripts\developer\build.ps1"
$installerWxs = Join-Path $repoRoot "packaging\windows\SelfSnapInstaller.wxs"
$bundleWxs = Join-Path $repoRoot "packaging\windows\SelfSnapBundle.wxs"

Initialize-CleanDirectory -Path $artifactRootPath
New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null
New-Item -ItemType Directory -Path $portableRoot -Force | Out-Null
New-Item -ItemType Directory -Path $wixWorkRoot -Force | Out-Null

Push-Location $repoRoot
try {
    & powershell.exe -ExecutionPolicy Bypass -File $buildScript -PythonExe $pythonFullPath
    Assert-LastExitCode "PyInstaller package build"

    $trayExe = Join-Path $distRoot "SelfSnapTray.exe"
    $workerExe = Join-Path $distRoot "SelfSnapWorker.exe"
    foreach ($requiredArtifact in @($trayExe, $workerExe)) {
        if (-not (Test-Path $requiredArtifact)) {
            throw "Expected compiled artifact is missing: $requiredArtifact"
        }
    }

    Copy-Item -Path $trayExe -Destination (Join-Path $stageRoot "SelfSnapTray.exe") -Force
    Copy-Item -Path $workerExe -Destination (Join-Path $stageRoot "SelfSnapWorker.exe") -Force
    $portableReadmePath = Join-Path $stageRoot "README.txt"
    Write-PortableReadme -Version $packageVersion -BuildLabel $BuildLabel -OutputPath $portableReadmePath
    Copy-Item -Path (Join-Path $stageRoot "*") -Destination $portableRoot -Recurse -Force

    $portableZipPath = Join-Path $artifactRootPath ("SelfSnap-{0}{1}-portable.zip" -f $packageVersion, $artifactSuffix)
    New-ZipFromDirectory -SourceDirectory $portableRoot -DestinationPath $portableZipPath

    & $workerExe --help | Out-Null
    Assert-LastExitCode "SelfSnapWorker portable smoke test"

    $wixToolset = Get-WixToolset
    $installerObjectPath = Join-Path $wixWorkRoot "SelfSnapInstaller.wixobj"
    $bundleObjectPath = Join-Path $wixWorkRoot "SelfSnapBundle.wixobj"
    $msiPath = Join-Path $artifactRootPath ("SelfSnap-{0}{1}-windows-x64.msi" -f $packageVersion, $artifactSuffix)
    $setupExePath = Join-Path $artifactRootPath ("SelfSnap-{0}{1}-windows-x64-setup.exe" -f $packageVersion, $artifactSuffix)

    & $wixToolset.Candle -nologo -arch x64 "-dProductVersion=$packageVersion" "-dStageDir=$stageRoot" -out $installerObjectPath $installerWxs
    Assert-LastExitCode "WiX installer compile"
    & $wixToolset.Light -nologo -sval -out $msiPath $installerObjectPath
    Assert-LastExitCode "WiX MSI link"

    & $wixToolset.Candle -nologo -ext WixBalExtension "-dProductVersion=$packageVersion" "-dMsiPath=$msiPath" -out $bundleObjectPath $bundleWxs
    Assert-LastExitCode "WiX bundle compile"
    & $wixToolset.Light -nologo -sval -ext WixBalExtension -out $setupExePath $bundleObjectPath
    Assert-LastExitCode "WiX setup EXE link"

    Get-ChildItem -Path $artifactRootPath -File | Sort-Object Name | ForEach-Object {
        Write-Host ("Created artifact: {0}" -f $_.FullName)
    }
}
finally {
    Pop-Location
}