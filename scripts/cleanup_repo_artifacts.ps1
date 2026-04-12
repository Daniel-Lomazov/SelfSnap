param(
    [switch]$ListOnly,
    [switch]$RepairAcl,
    [string[]]$Exclude = @()
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# ── What this script removes ─────────────────────────────────────────────────
#
#  Via git status (ignored + untracked):
#    .pytest_cache/, .pytest_tmp/, .pytest-work/, pytest-cache-files-*/
#    .ruff_cache/, .mypy_cache/, .hypothesis/
#    .coverage, coverage.xml, cov_annotate/
#    __pycache__/, *.pyc, *.pyo, *.pyd, pytest*.out
#    build/, dist/, *.egg-info/, .uv-cache/, tmp/, artifacts/
#    and any other git-ignored or untracked item
#
#  Via explicit sweep (catches files that may be committed/tracked by git):
#    cov_annotate/, .coverage, coverage.xml
#
#  Via recursive directory sweep under the repo tree:
#    __pycache__, .pytest_cache, .pytest_tmp, .pytest-work
#    .ruff_cache, .mypy_cache, .hypothesis, .uv-cache, *.egg-info
#
#  Via recursive file sweep:
#    *.pyc, *.pyo, *.pyd, pytest*.out
#
# Protected (never removed even if gitignored):
#    .venv/, venv/, .git/
#
# ─────────────────────────────────────────────────────────────────────────────

# Directories that are always protected — never removed even if gitignored.
$ProtectedTopLevel = [System.Collections.Generic.HashSet[string]]::new(
    [string[]]@('.venv', 'venv', '.git'),
    [StringComparer]::OrdinalIgnoreCase
)

# Explicit paths relative to repo root that are targeted even when tracked by git.
$ExplicitPaths = @(
    'cov_annotate'
    '.coverage'
    'coverage.xml'
)

# Directory names removed recursively anywhere in the tree.
$RecursiveDirNames = @(
    '__pycache__'
    '.pytest_cache'
    '.pytest_tmp'
    '.pytest-work'
    '.ruff_cache'
    '.mypy_cache'
    '.hypothesis'
    '.uv-cache'
)

# File patterns removed recursively anywhere in the tree.
$RecursiveFilePatterns = @(
    '*.pyc'
    '*.pyo'
    '*.pyd'
    'pytest*.out'
)

# ── Candidate collection ──────────────────────────────────────────────────────

function Get-ArtifactCandidates {
    param([string]$RepoRoot, [string[]]$ExcludeList)

    $seen       = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $candidates = [System.Collections.Generic.List[object]]::new()

    function Add-Candidate {
        param([string]$FullPath, [string]$Label)
        if (-not (Test-Path -LiteralPath $FullPath)) { return }
        $relPath = $FullPath.Substring($RepoRoot.Length).TrimStart('\').TrimEnd('\')
        if ([string]::IsNullOrWhiteSpace($relPath)) { return }
        $topLevel = $relPath.Split('\')[0]
        if ($ProtectedTopLevel.Contains($topLevel)) { return }
        if ($ExcludeList -contains $relPath) { return }
        if (-not $seen.Add($relPath)) { return }
        $item = Get-Item -LiteralPath $FullPath -Force
        $candidates.Add([pscustomobject]@{
            RelativePath = $relPath
            FullPath     = $item.FullName
            IsDirectory  = $item.PSIsContainer
            Label        = $Label
        })
    }

    # Pass 1: git status — ignored (!!) and untracked (??)
    $gitLines = & git -C $RepoRoot status --porcelain=v1 --ignored --untracked-files=all 2>&1
    foreach ($line in $gitLines) {
        if ($line.Length -lt 4) { continue }
        $code = $line.Substring(0, 2)
        if ($code -ne '!!' -and $code -ne '??') { continue }
        # git quotes paths that contain spaces or special characters — strip those quotes
        $rel  = $line.Substring(3).Trim().Trim('"').TrimEnd('/').Replace('/', '\')
        $lbl  = if ($code -eq '!!') { 'git-ignored' } else { 'untracked' }
        Add-Candidate -FullPath (Join-Path $RepoRoot $rel) -Label $lbl
    }

    # Pass 2: explicit known artifacts (catches committed files like coverage.xml)
    foreach ($rel in $ExplicitPaths) {
        Add-Candidate -FullPath (Join-Path $RepoRoot $rel) -Label 'explicit'
    }

    # Pass 3: recursive directory sweep
    foreach ($dirName in $RecursiveDirNames) {
        Get-ChildItem -Path $RepoRoot -Filter $dirName -Recurse -Directory -Force -ErrorAction SilentlyContinue |
            ForEach-Object { Add-Candidate -FullPath $_.FullName -Label 'recursive-dir' }
    }

    # Pass 4: recursive file sweep
    foreach ($pattern in $RecursiveFilePatterns) {
        Get-ChildItem -Path $RepoRoot -Filter $pattern -Recurse -File -Force -ErrorAction SilentlyContinue |
            ForEach-Object { Add-Candidate -FullPath $_.FullName -Label 'recursive-file' }
    }

    # Sort deepest paths first so children are removed before parents.
    return @($candidates | Sort-Object @{ Expression = { ($_.RelativePath -split '\\').Count }; Descending = $true }, RelativePath)
}

# ── Removal ───────────────────────────────────────────────────────────────────

function Remove-Artifact {
    param([pscustomobject]$Item)

    if (-not (Test-Path -LiteralPath $Item.FullPath)) {
        return [pscustomobject]@{ Path = $Item.RelativePath; Status = 'already-absent'; Note = '' }
    }

    try {
        Remove-Item -LiteralPath $Item.FullPath -Recurse -Force -ErrorAction Stop
        return [pscustomobject]@{ Path = $Item.RelativePath; Status = 'removed'; Note = '' }
    }
    catch {
        if (-not $RepairAcl) {
            return [pscustomobject]@{ Path = $Item.RelativePath; Status = 'failed'; Note = $_.Exception.Message }
        }
        try {
            $null = takeown /F $Item.FullPath /R /D Y 2>&1
            $null = icacls  $Item.FullPath /reset /T   2>&1
            Remove-Item -LiteralPath $Item.FullPath -Recurse -Force -ErrorAction Stop
            return [pscustomobject]@{ Path = $Item.RelativePath; Status = 'removed'; Note = 'ACL repaired' }
        }
        catch {
            return [pscustomobject]@{ Path = $Item.RelativePath; Status = 'failed'; Note = $_.Exception.Message }
        }
    }
}

# ── Main ──────────────────────────────────────────────────────────────────────

$candidates = Get-ArtifactCandidates -RepoRoot $repoRoot -ExcludeList $Exclude

if ($candidates.Count -eq 0) {
    Write-Host "No artifact candidates found under $repoRoot."
    exit 0
}

Write-Host "Artifact candidates under ${repoRoot}:"
$candidates |
    Select-Object Label,
                  @{ Name = 'Kind'; Expression = { if ($_.IsDirectory) { 'dir' } else { 'file' } } },
                  RelativePath |
    Format-Table -AutoSize |
    Out-String |
    Write-Host

if ($ListOnly) {
    exit 0
}

$results = foreach ($c in $candidates) { Remove-Artifact -Item $c }

$results | Format-Table Path, Status, Note -AutoSize | Out-String | Write-Host

$failed = @($results | Where-Object { $_.Status -eq 'failed' })
if ($failed.Count -gt 0) {
    Write-Warning "$($failed.Count) item(s) could not be removed. Run with -RepairAcl to attempt ACL repair."
}

Write-Host "Repo artifact cleanup complete."