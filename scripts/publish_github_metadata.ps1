param(
    [string]$Repo = "Daniel-Lomazov/SelfSnap",
    [switch]$PublishReleases
)

$ErrorActionPreference = "Stop"

function Get-ChangelogSection {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Tag
    )

    $changelogPath = Join-Path $PSScriptRoot "..\CHANGELOG.md"
    $content = Get-Content -LiteralPath $changelogPath -Raw -Encoding UTF8
    $marker = "## $Tag - "
    $start = $content.IndexOf($marker)
    if ($start -lt 0) {
        throw "CHANGELOG.md does not contain a section for $Tag."
    }

    $next = $content.IndexOf("`n## ", $start + $marker.Length)
    if ($next -lt 0) {
        return $content.Substring($start).Trim() + "`n"
    }
    return $content.Substring($start, $next - $start).Trim() + "`n"
}

function Assert-GhAuth {
    $null = & gh auth status 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub CLI is not authenticated. Run 'gh auth login -h github.com' first."
    }
}

Assert-GhAuth

$description = "Windows 11 local-first screenshot tray utility with Task Scheduler integration, offline-by-default runtime, and privacy-visible controls."
$topics = @(
    "windows",
    "windows-11",
    "python",
    "desktop-app",
    "screenshot",
    "task-scheduler",
    "tray-app",
    "local-first",
    "offline-first"
)

$repoEditArgs = @("repo", "edit", $Repo, "--description", $description)
foreach ($topic in $topics) {
    $repoEditArgs += @("--add-topic", $topic)
}
& gh @repoEditArgs

if (-not $PublishReleases) {
    Write-Host "Updated repo description and topics for $Repo."
    exit 0
}

$tags = @("v0.1.0", "v0.2.0", "v0.3.0", "v0.4.0", "v0.5.0", "v0.6.0", "v0.7.0")
$tempNotes = [System.IO.Path]::GetTempFileName()

try {
    foreach ($tag in $tags) {
        $notes = Get-ChangelogSection -Tag $tag
        Set-Content -LiteralPath $tempNotes -Value $notes -Encoding UTF8

        & gh release view $tag -R $Repo *> $null
        if ($LASTEXITCODE -eq 0) {
            & gh release edit $tag -R $Repo --title $tag --notes-file $tempNotes
        }
        else {
            & gh release create $tag -R $Repo --title $tag --notes-file $tempNotes
        }
    }
}
finally {
    Remove-Item -LiteralPath $tempNotes -Force -ErrorAction SilentlyContinue
}

Write-Host "Updated repo description/topics and published historical releases for $Repo."
