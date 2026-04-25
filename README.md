# SelfSnap Win11

SelfSnap Win11 is a Windows 11-only, local-first screenshot tray app for personal use. It captures all connected monitors on manual or scheduled runs, stores images locally, and records honest SQLite metadata about what happened.

Current version: `v1.3.2`. Technical release history lives in `CHANGELOG.md`.

This repository currently tracks the stable public release line on `main`.

SelfSnap is offline by default. The only user-triggered network actions are opening a browser for `Report Issue` and using `Check for Updates`, which queries the GitHub Releases API and optionally fetches the new release tag.
There is no telemetry or silent upload in normal runtime.

## Start here by need

Use this table as the main jump surface. Every linked README below links back to the others, so you can move between product overview, active docs, and archive material without losing your place.

| If you want to... | Start here |
|---|---|
| understand the product quickly | [README.md](README.md) |
| browse the full documentation map | [docs/README.md](docs/README.md) |
| install, update, reinstall, or uninstall | [docs/user/INSTALL_AND_UPDATE.md](docs/user/INSTALL_AND_UPDATE.md) |
| browse all current user docs | [docs/user/README.md](docs/user/README.md) |
| troubleshoot a problem | [docs/user/TROUBLESHOOTING.md](docs/user/TROUBLESHOOTING.md) |
| review commands and CLI behavior | [docs/user/CLI_REFERENCE.md](docs/user/CLI_REFERENCE.md) |
| review common UI and tray flows | [docs/user/WORKFLOWS.md](docs/user/WORKFLOWS.md) |
| change or validate product behavior | [docs/developer/README.md](docs/developer/README.md) |
| inspect archived or historical material | [docs/archive/README.md](docs/archive/README.md) |

## Current state

- Public stable `v1.3.2` Windows 11 utility with Fluent-style UI, responsive design, hardened setup and install flows, and downloadable Windows packages
- Current `main` is the stable public GitHub face of the app
- Hybrid tray plus Windows Task Scheduler model for recurring capture
- Source-based install with a checkout-local `.venv` is the primary supported path
- Successful `main` builds publish downloadable Windows artifacts through GitHub Actions
- Technical release history lives in [CHANGELOG.md](CHANGELOG.md)

## What SelfSnap covers

- Windows 11 only
- Logged-in desktop session only
- Manual capture and recurring schedules
- Local image output with configurable `png`, `jpeg`, or `webp` formats
- Local SQLite metadata and rotating text logs
- No cloud sync, telemetry, or stealth behavior

## Privacy and storage

SelfSnap stores screenshots locally. Screenshots may contain sensitive information such as messages, credentials, finance pages, or work material. v1 does not encrypt captures at rest. Use only on a machine and storage location you control.

Default app data lives under `%LOCALAPPDATA%\SelfSnap\`. Default image storage lives under `%USERPROFILE%\Pictures\SelfSnap\`. The OneDrive preset uses `%OneDrive%\Pictures\SelfSnap\` when available. For the full storage preset mapping, config fields, schedule schema, and runtime paths, use [docs/user/CONFIG_REFERENCE.md](docs/user/CONFIG_REFERENCE.md) and [docs/user/WORKFLOWS.md](docs/user/WORKFLOWS.md).

## Quick start

> **Important:** Always use the `.venv` created by `scripts/user/setup.ps1`. The Windows Store Python stub
> (default `python` on many Windows 11 machines) is Python 3.11 and is **not** used by SelfSnap.
> User-facing lifecycle scripts live under `scripts/user/`, and developer-only automation lives under `scripts/developer/`.
> All user scripts auto-detect `.venv\Scripts\python.exe` — no explicit `-PythonExe` flag needed.

### First install

```powershell
# 1. Create the virtual environment
powershell -ExecutionPolicy Bypass -File .\scripts\user\setup.ps1

# 2. Install the app, wrapper, and startup shortcut
powershell -ExecutionPolicy Bypass -File .\scripts\user\install.ps1
```

### Common commands after install

```powershell
SelfSnap tray
SelfSnap capture --trigger manual
SelfSnap diag
SelfSnap reinstall
```

### Common commands from source

```powershell
.venv\Scripts\Activate.ps1
python -m selfsnap tray
python -m selfsnap capture --trigger manual
python -m selfsnap diag
```

For the full lifecycle and command surface, use [docs/user/INSTALL_AND_UPDATE.md](docs/user/INSTALL_AND_UPDATE.md), [docs/user/CLI_REFERENCE.md](docs/user/CLI_REFERENCE.md), and [docs/user/README.md](docs/user/README.md).

## Where detailed guidance lives

The top-level README stays compact on purpose. The detailed operational and reference material lives here:

- [docs/README.md](docs/README.md): full documentation map and cross-hub routing
- [docs/user/README.md](docs/user/README.md): current user-facing setup, config, workflow, and troubleshooting guides
- [docs/user/INSTALL_AND_UPDATE.md](docs/user/INSTALL_AND_UPDATE.md): setup, install, update, reinstall, and uninstall guidance
- [docs/user/CLI_REFERENCE.md](docs/user/CLI_REFERENCE.md): full `selfsnap` command surface
- [docs/user/CONFIG_REFERENCE.md](docs/user/CONFIG_REFERENCE.md): config keys, storage behavior, and schedule schema
- [docs/user/WORKFLOWS.md](docs/user/WORKFLOWS.md): schedules, tray flows, Settings behavior, and day-to-day usage
- [docs/user/TROUBLESHOOTING.md](docs/user/TROUBLESHOOTING.md): diagnostics-first recovery steps and safe issue reporting
- [docs/developer/README.md](docs/developer/README.md): active product, architecture, and validation contract
- [docs/archive/README.md](docs/archive/README.md): archived historical and release material
- [scripts/README.md](scripts/README.md), [scripts/user/README.md](scripts/user/README.md), and [scripts/developer/README.md](scripts/developer/README.md): script entrypoint indexes

## Development, validation, and cleanup

```powershell
pytest
```

Full `pytest` runs enforce the repo coverage gate at 90%. Pytest temp directories are intentionally kept out of the repo under `%LOCALAPPDATA%\SelfSnap\pytest\tmp`, the pytest cache provider is disabled, and the pytest config explicitly ignores repo-local temp and cache folders such as `.pytest_cache`, `.pytest_tmp`, `.pytest-work`, and `pytest-cache-files-*`.

Use `scripts/developer/cleanup_repo_artifacts.ps1` to remove local artifacts such as `cov_annotate/`, `.coverage`, `coverage.xml`, `.pytest_cache/`, `.pytest_tmp/`, `.pytest-work/`, `pytest-cache-files-*`, `build/`, `dist/`, and `*.egg-info/`. Use `-ListOnly` to preview and `-RepairAcl` when ACL ownership blocks removal.

## Packaging and GitHub automation

- `scripts/developer/build.ps1` builds the raw `SelfSnapTray.exe` and `SelfSnapWorker.exe` binaries.
- `scripts/developer/package_windows.ps1` builds the portable ZIP, per-user MSI, and setup EXE under `artifacts/windows/`.
- `.github/workflows/ci.yml` keeps the repo healthy on pushes and pull requests with Windows-based compile smoke checks and `pytest`.
- `.github/workflows/package-main.yml` runs after a successful `CI` push to `main` and uploads downloadable Windows artifacts (`portable.zip`, `.msi`, `-setup.exe`) to the workflow run.
- `.github/workflows/release.yml` creates GitHub releases automatically for future version tags and attaches the Windows artifacts to the tagged release.
- `.github/workflows/issue-intake.yml` preprocesses new issues, applies managed labels, and posts a planning starter comment for maintainer triage.
- `Report Issue` always opens a browser-based GitHub issue flow. `SELFSNAP_GITHUB_REPO` can override the default issue destination if you are working from a fork.

## Documentation sync points

When a doc or user-visible behavior changes, these are the default go-to companions to review in the same pass:

- Setup, install, update, reinstall, or uninstall changes: [README.md](README.md), [docs/user/README.md](docs/user/README.md), [docs/user/INSTALL_AND_UPDATE.md](docs/user/INSTALL_AND_UPDATE.md), [docs/user/TROUBLESHOOTING.md](docs/user/TROUBLESHOOTING.md), and [scripts/user/README.md](scripts/user/README.md)
- CLI commands, tray actions, or common user flows: [README.md](README.md), [docs/user/CLI_REFERENCE.md](docs/user/CLI_REFERENCE.md), [docs/user/WORKFLOWS.md](docs/user/WORKFLOWS.md), and [docs/user/README.md](docs/user/README.md)
- Product, runtime, or validation contract changes: [docs/developer/README.md](docs/developer/README.md), [docs/developer/product-requirements-document-v1.md](docs/developer/product-requirements-document-v1.md), [docs/developer/software-requirements-specification-and-architecture-v1.md](docs/developer/software-requirements-specification-and-architecture-v1.md), and [docs/developer/validation-checklist.md](docs/developer/validation-checklist.md)
- Archive additions, removals, or reclassification: [docs/README.md](docs/README.md), [docs/archive/README.md](docs/archive/README.md), and the affected archive-folder README

## License

This repository is public for visibility and issue tracking, but the code remains under the proprietary personal-use terms in `LICENSE`.
