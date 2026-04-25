# SelfSnap Win11

SelfSnap Win11 is a Windows 11-only, local-first screenshot utility for personal use. It captures screenshots of all connected monitors on recurring schedules, stores them locally, and records honest metadata about what happened.

Current version: `v1.1.1`. Technical release history lives in `CHANGELOG.md`.

This repository currently tracks an active preview build, not a stable release.

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

## Project status

- Public `v1.1.1` Windows 11 utility with Fluent-style UI, responsive design, and hardened setup/install flows
- Active preview build for personal-use iteration, not a stable release
- Source-based install is the primary supported path
- Public release posture is focused on privacy-minded Windows power users
- Current trust and release posture is summarized in this README, first-run, Settings, and the product docs; archived v1 release-gate notes now live in `docs/archive/releases/common.release-readiness-criteria-v1.0.md`

## License

This repository is public for visibility and issue tracking, but the code remains under the proprietary personal-use terms in `LICENSE`.

## Current release

`v1.1.1` is the current preview build with setup and install recovery fixes, schema-4 config support, and documentation alignment across the script and docs surfaces. It is not a stable release, and the install and documentation flow can still change between iterations.

- **Fluent-style Settings redesign.** Complete visual refresh with responsive card/panel layouts that adapt to window width, improved text wrapping, and accessible keyboard navigation.
- **Enhanced diagnostics and observability.** New diagnostics surface in Settings shows scheduler sync status, storage metrics, retention policy, and operational context in real-time.
- **Responsive schedule editor.** Schedule list and editor panels reflow between stacked (narrow) and side-by-side (wide) layouts with auto-fit column widths to prevent truncation.
- **Runtime hardening.** Setup now recovers more reliably from locked `.venv\Scripts` tool executables, install no longer trips over the current schema-4 config, and local `.venv` interpreter enforcement keeps source launches on the correct environment.
- **Expanded internal documentation.** The README/docs/script navigation was tightened, preview posture is called out consistently, and current config-schema behavior is documented directly in the install, troubleshooting, and config reference docs.

For the full implementation-facing release history, see [`CHANGELOG.md`](CHANGELOG.md).

## v1 scope

- Windows 11 only
- Logged-in desktop session only
- Manual capture
- Recurring schedules using a hybrid tray and Windows Task Scheduler model
- Local image output with configurable `png`, `jpeg`, or `webp` formats
- Composite capture by default, with optional per-monitor output
- Local SQLite metadata
- Rotating text logs
- Minimal tray control surface
- Source-based install with a wrapper script and full paths
- No cloud sync, telemetry, or stealth behavior

## Privacy warning

SelfSnap stores screenshots locally. Screenshots may contain sensitive information such as messages, credentials, finance pages, or work material. v1 does not encrypt captures at rest. Use only on a machine and storage location you control.
The first-run and Settings surfaces repeat this warning in-product.

## Known 1.0 limitations

- No encryption at rest for capture files in v1.
- Wake-from-sleep capture is best effort, not guaranteed.
- No guarantee of scheduled capture during full shutdown or logged-out desktop states.
- Logged-in desktop session is required for capture.
- Windows 11 only.
- Source-based install is the supported distribution path.
- No cloud sync or telemetry.
- No full history browser or search UI.

## Quick start

> **Important:** Always use the `.venv` created by `scripts/user/setup.ps1`. The Windows Store Python stub
> (default `python` on many Windows 11 machines) is Python 3.11 and is **not** used by SelfSnap.
> User-facing lifecycle scripts live under `scripts/user/`, and developer-only automation lives under `scripts/developer/`.
> All user scripts auto-detect `.venv\Scripts\python.exe` — no explicit `-PythonExe` flag needed.

### First install (no prior SelfSnap installation)

```powershell
# 1. Create the virtual environment (uses uv + Python 3.12 when available)
powershell -ExecutionPolicy Bypass -File .\scripts\user\setup.ps1

# 2. Install the app, wrapper, and startup shortcut
powershell -ExecutionPolicy Bypass -File .\scripts\user\install.ps1
```

`scripts/user/install.ps1` automatically:
- Uses `.venv\Scripts\python.exe` (Python 3.12 via uv)
- Creates `%LOCALAPPDATA%\SelfSnap\bin\SelfSnap.cmd` wrapper
- Adds the bin directory to your user `PATH`
- Creates a startup shortcut if `start_tray_on_login` is enabled

For the full lifecycle surface, use [docs/user/INSTALL_AND_UPDATE.md](docs/user/INSTALL_AND_UPDATE.md) and [docs/user/CLI_REFERENCE.md](docs/user/CLI_REFERENCE.md).

### Already installed — just reinstall

If SelfSnap is already installed (wrapper on PATH), the fastest path is:

```powershell
# From any terminal — no need to be in the repo root
SelfSnap reinstall
```

Or from within the repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\user\reinstall.ps1
```

Or from the tray menu: **Reinstall**.

### Run from source (no install required)

```powershell
# Activate the venv first
.venv\Scripts\Activate.ps1

# Start the tray
python -m selfsnap tray

# Take a manual capture
python -m selfsnap capture --trigger manual

# Run a scheduled capture for a specific schedule
python -m selfsnap capture --trigger scheduled --schedule-id morning

# Sync Windows Task Scheduler tasks from config
python -m selfsnap sync-scheduler

# Catch up missed schedule slots (run on startup to reconcile gaps)
python -m selfsnap reconcile

# Run diagnostics
python -m selfsnap doctor
python -m selfsnap diag

# Print the installed version
python -m selfsnap --version
```

### Run after install

Once `install.ps1` has been run, the `SelfSnap` wrapper is on your `PATH`:

```powershell
# Start the tray
SelfSnap tray

# Take a manual capture
SelfSnap capture --trigger manual

# Run a scheduled capture
SelfSnap capture --trigger scheduled --schedule-id morning

# Sync Task Scheduler
SelfSnap sync-scheduler

# Reconcile missed slots
SelfSnap reconcile

# Diagnostics
SelfSnap doctor
SelfSnap diag

# Check for updates without installing
SelfSnap update --check-only

# Reinstall from current checkout
SelfSnap reinstall

# Uninstall (prompts for confirmation)
SelfSnap uninstall
```

## Runtime storage

SelfSnap splits image storage from app data by default.

```text
%LOCALAPPDATA%\SelfSnap\
  config\config.json
  data\selfsnap.db
  logs\selfsnap.log
  bin\SelfSnap.cmd

%USERPROFILE%\Pictures\SelfSnap\
  captures\YYYY\MM\DD\...
  archive\YYYY\MM\DD\...
```

If the storage preset is `onedrive_pictures`, image storage switches to:

```text
%OneDrive%\Pictures\SelfSnap\
  captures\YYYY\MM\DD\...
  archive\YYYY\MM\DD\...
```

## Storage preset mapping

| Settings label | Config value | Capture root | Archive root |
|---|---|---|---|
| `Local Pictures` | `local_pictures` | `%USERPROFILE%\Pictures\SelfSnap\captures` | `%USERPROFILE%\Pictures\SelfSnap\archive` |
| `OneDrive Pictures` | `onedrive_pictures` | `%OneDrive%\Pictures\SelfSnap\captures` | `%OneDrive%\Pictures\SelfSnap\archive` |
| `Custom Folder` | `custom` | user-defined | user-defined |

If `%OneDrive%` is not set, SelfSnap resolves the OneDrive preset through `%USERPROFILE%\OneDrive`. The OneDrive preset is only accepted when the resolved base path already exists and is writable.

If a previously valid OneDrive root becomes unavailable (for example OneDrive is paused, moved, or disconnected), capture writes can fail. Recovery path: switch to `Local Pictures` in `Settings`, save, and re-run `selfsnap diag` to verify paths.

## Troubleshooting

### Start with diagnostics

```powershell
SelfSnap doctor
SelfSnap diag
```

- Use `doctor` to confirm runtime dependencies and launch assumptions.
- Use `diag` to capture safe state details such as version, paths, scheduler sync status, and latest capture outcome.

### Common recovery actions

- Scheduler seems stuck or disabled unexpectedly: run `selfsnap sync-scheduler`, then check `scheduler_sync_ok` in `selfsnap diag`.
- Captures missing after sleep/wake: this can be expected for some sleep windows; confirm missed/failed status in tray surfaces and keep machine awake for critical capture intervals.
- OneDrive preset failing: switch storage preset to `Local Pictures`, save, and retry manual capture.
- Startup issues after updates: run `SelfSnap reinstall` from the repository checkout.

### Reporting issues safely

- Use tray `Report Issue` so the browser opens a prefilled issue template.
- Include your short description plus `selfsnap diag` output summary.
- SelfSnap never auto-attaches screenshots, logs, local file paths, or database content.

For the broader recovery and reporting path, use [docs/user/TROUBLESHOOTING.md](docs/user/TROUBLESHOOTING.md) and the current user-doc hub at [docs/user/README.md](docs/user/README.md).

## Documentation hubs

- [docs/README.md](docs/README.md): documentation index and cross-hub map
- [docs/user/README.md](docs/user/README.md): entry point for current user-facing setup, CLI, troubleshooting, config, and workflow guides
- [docs/developer/README.md](docs/developer/README.md): entry point for the active developer-facing product contract, architecture, and validation docs
- [docs/archive/README.md](docs/archive/README.md): entry point for historical customer baseline, starter-kit, release, and planning references

## Further documentation

If you are using the current source checkout rather than reading historical design material, start with:

- [docs/user/README.md](docs/user/README.md)
- [docs/user/INSTALL_AND_UPDATE.md](docs/user/INSTALL_AND_UPDATE.md)
- [docs/user/CLI_REFERENCE.md](docs/user/CLI_REFERENCE.md)
- [docs/user/TROUBLESHOOTING.md](docs/user/TROUBLESHOOTING.md)
- [docs/user/CONFIG_REFERENCE.md](docs/user/CONFIG_REFERENCE.md)
- [docs/user/WORKFLOWS.md](docs/user/WORKFLOWS.md)

If you are maintaining the product rather than just using it, start with [docs/developer/README.md](docs/developer/README.md) and then use the active PRD, runtime contract, and validation checklist there.

If you are tracing older decisions or release evidence, start with [docs/archive/README.md](docs/archive/README.md).

## Report Issue

- `Report Issue` is available from the tray menu and is the default tray action where the Windows shell supports pystray default activation.
- The dialog asks for a short paragraph and can include only safe diagnostics limited to product/runtime metadata such as app version, storage preset, scheduler sync state, and the latest outcome code.
- SelfSnap does not attach screenshots, local file paths, logs, or database contents automatically.
- Browser mode is the only supported reporting mode.
- SelfSnap always opens a prefilled GitHub issue page in the browser and leaves the final submission under user control.
- No silent upload or background issue submission occurs.
- `SELFSNAP_GITHUB_REPO` can override the default issue destination if you are working from a fork.

## How to add scheduled captures

Open `Settings` and go to `Schedules`. A new schedule starts with these defaults:

- `Every 1 day`
- `start date = today`
- `start time = now` in local time

Supported formats are `Every N seconds/minutes/hours/days/weeks/months/years` with a start date and start time.

To add a schedule:

1. Enter a label.
2. Choose `Every N`.
3. Choose a unit: `seconds`, `minutes`, `hours`, `days`, `weeks`, `months`, or `years`.
4. Set the start date and start time.
5. Leave `enabled` on if you want the schedule active.
6. Click `Add`.

The defaults are `Every 1 day`, `start date = today`, and `start time = now` in local time. You can type the date and time by hand if you want a custom anchor.

To edit a schedule:

1. Select one schedule in the list.
2. Edit the fields in place (including the `Enabled` checkbox to pause it).
3. Click `Save` in the main action bar to apply — no need to click the inline "Save" first.

To delete schedules:

1. Select one or more schedules in the list.
2. Click `Delete`.

Selection rules:

- One selected schedule enables edit, save, cancel, and delete.
- Multiple selected schedules disable add and edit controls.
- Multi-select is for deleting several schedules at once.

Schedule timing rules:

- `Every N unit` means the schedule repeats from its saved start date and start time.
- `months` and `years` skip invalid calendar dates instead of moving to the last day of the period.
- High-frequency schedules such as `seconds` and `minutes` are tray-managed while the tray is running.
- Coarser schedules such as `hours`, `days`, `weeks`, `months`, and `years` are Windows Task Scheduler-backed.

For broader day-to-day tray and Settings flows, use [docs/user/WORKFLOWS.md](docs/user/WORKFLOWS.md).

## Config reference

See [docs/user/config.example.json](docs/user/config.example.json) for the full schema.

Important fields:

- `app_enabled`: global enable or disable for scheduled capture
- `first_run_completed`: whether the first-run setup gate has been completed
- `storage_preset`: `local_pictures`, `onedrive_pictures`, or `custom`
- `capture_storage_root`: explicit output folder for image files
- `archive_storage_root`: explicit archive folder for retention moves
- `retention_mode`: `keep_forever` or `keep_days`
- `retention_days`: required only when `retention_mode` is `keep_days`
- `purge_enabled`: when `true`, archived files are permanently deleted after `retention_grace_days` (default `false`)
- `retention_grace_days`: days after archiving before permanent deletion (default `30`); only active when `purge_enabled` is `true`
- `capture_mode`: `composite` (single stitched PNG, default) or `per_monitor` (one file per display)
- `image_format`: `png` (default), `jpeg`, or `webp`
- `image_quality`: 1–100 quality for JPEG/WebP (default `85`); ignored for PNG
- `start_tray_on_login`: controls the Startup-folder shortcut
- `show_last_capture_status`: toggles the passive latest-status line in the tray menu
- `notify_on_failed_or_missed`: toggles notifications for failed or missed events
- `notify_on_every_capture`: toggles notifications for all successful captures
- `show_capture_overlay`: toggles the brief on-screen overlay after successful capture
- `wake_for_scheduled_captures`: best-effort scheduler wake setting, default `false`
- `scheduler_sync_state`: `ok` or `failed`; when `failed`, manual capture still works and scheduled capture is blocked
- `settings_window_width` and `settings_window_height`: legacy geometry fields retained for compatibility
- `schedules`: list of recurring schedule entries with an internal `schedule_id`, plus `label`, `interval_value`, `interval_unit`, `start_date_local`, `start_time_local`, and `enabled`

For the full schema, examples, and config notes, use [docs/user/CONFIG_REFERENCE.md](docs/user/CONFIG_REFERENCE.md) and [docs/user/config.example.json](docs/user/config.example.json).

## Settings and reset behavior

- The settings window is resizable in both directions, uses tighter spacing, and opens at a stable minimum size instead of auto-remembering transient resize changes.
- Manual capture and background tray refreshes do not mutate the open settings window state.
- Tray `Capture Now` runs through a separate background worker so capture-side DPI or monitor handling cannot resize the settings window.
- Storage preset selection updates both capture and archive roots together.
- Editing either path manually switches the preset to `custom`.
- **Save** writes changes to disk immediately and keeps the window open. The button briefly shows `✓ Saved`. Editing a schedule's fields (including Enabled) and clicking Save is enough — no need to click the inline schedule "Save" first.
- **Close** closes the settings window.
- `Reset Capture History` permanently removes SelfSnap capture files, archive files, DB history, logs, config, startup shortcut, and scheduled tasks, then relaunches into first run.
- Reset is not uninstall: installed app files, wrapper scripts, and repo files stay in place.
- The tray exposes `Settings`, `Reinstall`, `Check for Updates`, `Uninstall`, `Restart`, and `Exit` (in that order at the bottom of the menu).
- `Restart` is a single button directly above `Exit`.
- `Reinstall` is offline and preserves user data.
- `Check for Updates` queries the GitHub Releases API, compares the latest tag against the installed version, and does nothing if already current. When a newer release is found it offers to fetch and install it; the window stays open if you decline.
- `Uninstall → Keep User Data` removes only startup/task/install links.
- `Uninstall → Remove All User Data` removes SelfSnap-owned config, DB, logs, captures, archive files, and app temp data, but not the repo checkout or `.venv`.
- Background tray, startup, and scheduled operations do not open a visible console window.

## First run and tray behavior

- The tray app shows a first-run setup dialog before scheduled capture can become active.
- Manual capture remains available even if setup is not completed.
- Global disable removes scheduled tasks instead of letting them run and skip.
- Individual disabled schedules are removed from Task Scheduler until re-enabled.
- A scheduler sync failure leaves the saved config in place, shows a persistent tray warning, and blocks scheduled captures until sync succeeds.
- Missed scheduled slots are recorded during reconciliation within roughly one minute of tray startup or resume.

## Development

If you are changing runtime, product, or validation behavior rather than just using SelfSnap, start with [docs/developer/README.md](docs/developer/README.md).

Script indexes:

- `scripts/README.md`: top-level script layout
- `scripts/user/README.md`: user-facing lifecycle entrypoints
- `scripts/developer/README.md`: developer-only maintenance and packaging helpers

## Documentation sync points

When a doc or user-visible behavior changes, these are the default go-to companions to review in the same pass:

- Setup, install, update, reinstall, or uninstall changes: [README.md](README.md), [docs/user/README.md](docs/user/README.md), [docs/user/INSTALL_AND_UPDATE.md](docs/user/INSTALL_AND_UPDATE.md), [docs/user/TROUBLESHOOTING.md](docs/user/TROUBLESHOOTING.md), and [scripts/user/README.md](scripts/user/README.md)
- CLI commands, tray actions, or common user flows: [README.md](README.md), [docs/user/CLI_REFERENCE.md](docs/user/CLI_REFERENCE.md), [docs/user/WORKFLOWS.md](docs/user/WORKFLOWS.md), and [docs/user/README.md](docs/user/README.md)
- Product, runtime, or validation contract changes: [docs/developer/README.md](docs/developer/README.md), [docs/developer/product-requirements-document-v1.md](docs/developer/product-requirements-document-v1.md), [docs/developer/software-requirements-specification-and-architecture-v1.md](docs/developer/software-requirements-specification-and-architecture-v1.md), and [docs/developer/validation-checklist.md](docs/developer/validation-checklist.md)
- Archive additions, removals, or reclassification: [docs/README.md](docs/README.md), [docs/archive/README.md](docs/archive/README.md), and the affected archive-folder README

```powershell
pytest
ruff check .
mypy src
```

Pytest temp directories are intentionally kept out of the repo under `%LOCALAPPDATA%\SelfSnap\pytest\tmp`, and the pytest cache provider is disabled to avoid `.pytest_cache` and `pytest-cache-files-*` clutter in the workspace.

Use `scripts/developer/cleanup_repo_artifacts.ps1` to remove all local artifact and cache folders. It covers:

- Coverage data: `cov_annotate/`, `.coverage`, `coverage.xml`
- Bytecode caches: `__pycache__/` (recursive), `*.pyc` / `*.pyo` / `*.pyd`
- Test caches: `.pytest_cache/`, `.pytest_tmp/`, `.pytest-work/`, `pytest-cache-files-*/`
- Tool caches: `.ruff_cache/`, `.mypy_cache/`, `.hypothesis/`, `.uv-cache/`
- Build outputs: `build/`, `dist/`, `*.egg-info/`
- Any other git-ignored or untracked file

`.venv/` and `.git/` are always protected.

```powershell
# Preview what would be removed
powershell -ExecutionPolicy Bypass -File .\scripts\developer\cleanup_repo_artifacts.ps1 -ListOnly

# Remove all artifacts
powershell -ExecutionPolicy Bypass -File .\scripts\developer\cleanup_repo_artifacts.ps1

# Attempt ACL repair (relaunches elevated via UAC), then remove
powershell -ExecutionPolicy Bypass -File .\scripts\developer\cleanup_repo_artifacts.ps1 -RepairAcl

# Exclude specific paths from removal
powershell -ExecutionPolicy Bypass -File .\scripts\developer\cleanup_repo_artifacts.ps1 -Exclude ".coverage","coverage.xml"
```

The setup script prefers a uv-managed Python 3.12 interpreter when `uv` is installed, then falls back to a normal `python` or `py` launcher on PATH. If you need to force a specific interpreter, pass it explicitly:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\user\setup.ps1 -PythonPreference "C:\Path\To\python.exe"
```

## Packaging

Source-based install is the v1 acceptance path.

Optional next-step packaging:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\developer\build.ps1
```

This optional build is prepared to create:

- `SelfSnapTray.exe` as a windowless tray executable
- `SelfSnapWorker.exe` as a windowless scheduled worker executable

## GitHub automation

- `.github/workflows/ci.yml` keeps the repo healthy on pushes and pull requests with Windows-based compile smoke checks and `pytest`.
- `.github/workflows/release.yml` creates GitHub releases automatically for future version tags and can also be run manually for existing historical tags.
- `.github/workflows/issue-intake.yml` preprocesses new issues, applies managed labels, and posts a planning starter comment for maintainer triage.
- `.github/ISSUE_TEMPLATE/report_issue.md` is the template used by the in-app issue reporting flow.
- `scripts/developer/publish_github_metadata.ps1` updates the repo description/topics and can publish historical releases once `gh auth login` is valid.

## Known limitations

- v1 is Windows 11 only.
- Wake-for-scheduled-captures is best-effort and Windows-dependent.
- Missed scheduled slots are recorded during tray reconciliation; they are not retried automatically.
- Full shutdown is not capturable and is never inferred from image content.
- Mixed-DPI and some protected-content cases should be validated on real hardware.
- On Windows virtual environments backed by `uv`, launching the tray from `.venv\Scripts\pythonw.exe` can show a parent `.venv` `pythonw.exe` plus a child `uv`-backed `pythonw.exe` in Task Manager. Current validation has not shown duplicate tray icons or duplicate user-visible behavior from this alone. Treat it as a process-model artifact unless you also see duplicate icons, duplicate notifications, or duplicate Settings windows.
