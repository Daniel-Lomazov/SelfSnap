# SelfSnap Win11

SelfSnap Win11 is a Windows 11-only, local-first screenshot utility for personal use. It captures a composite image of all connected monitors at configured daily times, stores the image locally, and records honest metadata about what happened.

## Current release

This release keeps background work console-free and adds:

- hidden tray/startup/scheduled background launches
- storage presets for `Local Pictures`, `OneDrive`, and `Custom`
- a destructive `Reset Capture History` flow that returns the app to first-run state
- a resizable, scroll-safe settings window
- a tray `Report Issue` flow that opens or creates GitHub issues without uploading screenshots automatically
- data-preserving reinstall by default

## v1 scope

- Windows 11 only
- Logged-in desktop session only
- Manual capture
- Multiple daily schedules through Windows Task Scheduler
- Local PNG output
- Local SQLite metadata
- Rotating text logs
- Minimal tray control surface
- Source-based install with a wrapper script and full paths
- No cloud sync, telemetry, or stealth behavior

## Privacy warning

SelfSnap stores screenshots locally. Screenshots may contain sensitive information such as messages, credentials, finance pages, or work material. v1 does not encrypt captures at rest. Use only on a machine and storage location you control.

## Quick start

1. Install Python 3.12 on Windows 11. Python 3.11 is also supported.
2. From the repository root, run the setup script.
3. Activate the virtual environment:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
.venv\Scripts\Activate.ps1
```

4. Run diagnostics:

```powershell
selfsnap doctor
selfsnap diag
```

5. Start the tray app:

```powershell
selfsnap tray
```

6. Trigger a manual capture:

```powershell
selfsnap capture --trigger manual
```

7. Optional source-based install with wrapper and startup shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -PythonExe python
```

If your Python environment uses a nonstandard `pythonw.exe`, pass it explicitly:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -PythonExe python -PythonwExe "C:\Path\To\pythonw.exe"
```

If you want a lean runtime environment without development tools, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -NoDev
```

If you change Python versions, rebuild the environment instead of reusing the old `.venv`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
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
| `OneDrive` | `onedrive_pictures` | `%OneDrive%\Pictures\SelfSnap\captures` | `%OneDrive%\Pictures\SelfSnap\archive` |
| `Custom` | `custom` | user-defined | user-defined |

If `%OneDrive%` is not set, SelfSnap resolves the OneDrive preset through `%USERPROFILE%\OneDrive`. The OneDrive preset is only accepted when the resolved base path already exists and is writable.

## Docs layout

- `docs/customer_baseline/`: original customer baseline documents that should change rarely
- `docs/implementation/`: implementation-facing PRD, architecture, QA/privacy, and validation docs
- `docs/README.md`: documentation index

## Commands

```powershell
selfsnap tray
selfsnap capture --trigger manual
selfsnap capture --trigger scheduled --schedule-id morning
selfsnap reconcile
selfsnap sync-scheduler
selfsnap diag
```

If `scripts/install.ps1` has been run, the wrapper command is:

```powershell
$env:LOCALAPPDATA\SelfSnap\bin\SelfSnap.cmd tray
$env:LOCALAPPDATA\SelfSnap\bin\SelfSnap.cmd capture --trigger manual
```

## Report Issue

- `Report Issue` is available from the tray menu and is the default tray action where the Windows shell supports pystray default activation.
- The dialog asks for a short paragraph and can include only safe diagnostics such as app version, storage preset, scheduler sync state, and the latest outcome code.
- SelfSnap does not attach screenshots, local file paths, logs, or database contents automatically.
- If `SELFSNAP_GITHUB_TOKEN`, `GH_TOKEN`, or `GITHUB_TOKEN` is present, SelfSnap can create the GitHub issue directly through the API.
- Otherwise SelfSnap opens a prefilled GitHub issue page in the browser and leaves the final submission under user control.
- `SELFSNAP_GITHUB_REPO` can override the default issue destination if you are working from a fork.

## Config reference

See `sample/config.example.json` for the full schema.

Important fields:

- `app_enabled`: global enable or disable for scheduled capture
- `first_run_completed`: whether the first-run setup gate has been completed
- `storage_preset`: `local_pictures`, `onedrive_pictures`, or `custom`
- `capture_storage_root`: explicit output folder for PNG files
- `archive_storage_root`: explicit archive folder for retention moves
- `retention_mode`: `keep_forever` or `keep_days`
- `retention_days`: required only when `retention_mode` is `keep_days`
- `start_tray_on_login`: controls the Startup-folder shortcut
- `show_last_capture_status`: toggles the passive latest-status line in the tray menu
- `notify_on_failed_or_missed`: toggles notifications for failed or missed events
- `notify_on_every_capture`: toggles notifications for all successful captures
- `show_capture_overlay`: toggles the brief on-screen overlay after successful capture
- `wake_for_scheduled_captures`: best-effort scheduler wake setting, default `false`
- `scheduler_sync_state`: `ok` or `failed`; when `failed`, manual capture still works and scheduled capture is blocked
- `settings_window_width` and `settings_window_height`: legacy geometry fields retained for compatibility
- `schedules`: list of daily `HH:MM` schedule entries

## Settings and reset behavior

- The settings window is resizable and scrollable, but it opens at a stable minimum size instead of auto-remembering transient resize changes.
- Manual capture and background tray refreshes do not mutate the open settings window state.
- Tray `Capture Now` runs through a separate background worker so capture-side DPI or monitor handling cannot resize the settings window.
- The settings window opens at a larger minimum size to avoid clipped controls and text.
- Storage preset selection updates both capture and archive roots together.
- Editing either path manually switches the preset to `custom`.
- `Reset Capture History` permanently removes SelfSnap capture files, archive files, DB history, logs, config, startup shortcut, and scheduled tasks, then relaunches into first run.
- Reset is not uninstall: installed app files, wrapper scripts, and repo files stay in place.
- Reinstall is non-destructive by default and preserves user data and settings unless you separately choose cleanup.
- Background tray, startup, and scheduled operations do not open a visible console window.

## First run and tray behavior

- The tray app shows a first-run setup dialog before scheduled capture can become active.
- Manual capture remains available even if setup is not completed.
- Global disable removes scheduled tasks instead of letting them run and skip.
- Individual disabled schedules are removed from Task Scheduler until re-enabled.
- A scheduler sync failure leaves the saved config in place, shows a persistent tray warning, and blocks scheduled captures until sync succeeds.
- Missed scheduled slots are recorded during reconciliation within roughly one minute of tray startup or resume.

## Development

```powershell
pytest
ruff check .
mypy src
```

Pytest temp directories are intentionally kept out of the repo under `%LOCALAPPDATA%\SelfSnap\pytest\tmp`, and the pytest cache provider is disabled to avoid `.pytest_cache` and `pytest-cache-files-*` clutter in the workspace.

If `.pytest_tmp` or `.pytest-work` still exist in the repo root with old timestamps, treat them as legacy leftovers from earlier runs. Current pytest configuration should not recreate them.

If stale pytest artifact folders remain from older runs and normal deletion fails, use the dedicated cleanup script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_pytest_artifacts.ps1 -ListOnly
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_pytest_artifacts.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_pytest_artifacts.ps1 -RepairAcl
```

`-RepairAcl` attempts a UAC-elevated ownership repair for legacy ACL-poisoned folders. Add `-IncludeLocalAppData` only if you also want to remove `%LOCALAPPDATA%\SelfSnap\pytest`.

The setup script prefers a uv-managed Python 3.12 interpreter when `uv` is installed, then falls back to a normal `python` or `py` launcher on PATH. If you need to force a specific interpreter, pass it explicitly:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -PythonPreference "C:\Path\To\python.exe"
```

## Packaging

Source-based install is the v1 acceptance path.

Optional next-step packaging:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

This optional build is prepared to create:

- `SelfSnapTray.exe` as a windowless tray executable
- `SelfSnapWorker.exe` as a windowless scheduled worker executable

## GitHub automation

- `.github/workflows/ci.yml` keeps the repo healthy on pushes and pull requests with Windows-based compile smoke checks and `pytest`.
- `.github/workflows/issue-intake.yml` preprocesses new issues, applies managed labels, and posts a planning starter comment for the next local-agent session.
- `.github/ISSUE_TEMPLATE/report_issue.md` is the template used by the in-app issue reporting flow.

## Known limitations

- v1 is Windows 11 only.
- v1 does not implement per-monitor output files.
- Wake-for-scheduled-captures is best-effort and Windows-dependent.
- Missed scheduled slots are recorded during tray reconciliation; they are not retried automatically.
- Full shutdown is not capturable and is never inferred from image content.
- Mixed-DPI and some protected-content cases should be validated on real hardware.
- On Windows virtual environments backed by `uv`, launching the tray from `.venv\Scripts\pythonw.exe` can show a parent `.venv` `pythonw.exe` plus a child `uv`-backed `pythonw.exe` in Task Manager. Current validation has not shown duplicate tray icons or duplicate user-visible behavior from this alone. Treat it as a process-model artifact unless you also see duplicate icons, duplicate notifications, or duplicate Settings windows.
