# Developer Scripts

These scripts are for repository maintenance, validation, packaging, and publishing work.
They are not required for everyday SelfSnap use after the user lifecycle scripts have completed.
They back both the local packaging lane and the GitHub Actions artifact-publishing flow.

Run them from the repository root:

- `scripts/developer/build.ps1`: build optional PyInstaller tray and worker executables
- `scripts/developer/package_windows.ps1`: build the downloadable Windows distribution artifacts (portable zip, per-user MSI, setup EXE)
- `scripts/developer/smoke_test.ps1`: reinstall through the script entrypoint unless `-SkipInstall` is used, then run wrapper diagnostics and a manual capture
- `scripts/developer/cleanup_pytest_artifacts.ps1`: remove pytest-specific cache and temp directories, with optional ACL repair
- `scripts/developer/cleanup_repo_artifacts.ps1`: remove broader repo-local artifacts such as coverage output, caches, build outputs, and ignored clutter
- `scripts/developer/publish_github_metadata.ps1`: update GitHub repo metadata and optionally publish historical releases through `gh`

Use these when validating release readiness, cleaning the workspace, packaging binaries, or maintaining the GitHub project surface.
