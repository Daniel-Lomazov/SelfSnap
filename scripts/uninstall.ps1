$ErrorActionPreference = "Stop"

$appRoot = Join-Path $env:LOCALAPPDATA "SelfSnap"
$binRoot = Join-Path $appRoot "bin"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = Join-Path $startupDir "SelfSnap Win11.lnk"

if (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath -Force
}

$taskNames = schtasks /Query /FO CSV /NH 2>$null |
    ForEach-Object {
        if ($_ -match '^"([^"]+)"') { $matches[1] }
    } |
    Where-Object { $_ -like "\SelfSnap.Capture.*" }

foreach ($taskName in $taskNames) {
    schtasks /Delete /TN ($taskName -replace '^\\', '') /F | Out-Null
}

if (Test-Path $binRoot) {
    Remove-Item $binRoot -Recurse -Force
}

Write-Host "SelfSnap binaries and scheduled tasks removed."
Write-Host "Config, database, logs, and captures under $appRoot were preserved."
