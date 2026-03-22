# SelfSnap Win11

SelfSnap Win11 is a Windows 11-only, local-first screenshot utility for personal use. It captures a composite image of all connected monitors at configured daily times, stores the image locally, and records honest metadata about what happened.

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

## Config reference

See `sample/config.example.json` for the full schema.

Important fields:

- `app_enabled`: global enable or disable for scheduled capture
- `first_run_completed`: whether the first-run setup gate has been completed
- `capture_storage_root`: output folder for PNG files, default `%USERPROFILE%\Pictures\SelfSnap\captures`
- `archive_storage_root`: archive folder for retention moves, default `%USERPROFILE%\Pictures\SelfSnap\archive`
- `retention_mode`: `keep_forever` or `keep_days`
- `retention_days`: required only when `retention_mode` is `keep_days`
- `start_tray_on_login`: controls the Startup-folder shortcut
- `show_last_capture_status`: toggles the passive latest-status line in the tray menu
- `notify_on_failed_or_missed`: toggles notifications for failed or missed events
- `notify_on_every_capture`: toggles notifications for all successful captures
- `show_capture_overlay`: toggles the brief on-screen overlay after successful capture
- `wake_for_scheduled_captures`: best-effort scheduler wake setting, default `false`
- `scheduler_sync_state`: `ok` or `failed`; when `failed`, manual capture still works and scheduled capture is blocked
- `schedules`: list of daily `HH:MM` schedule entries

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

- `SelfSnapTray.exe`
- `SelfSnapWorker.exe`

## Known limitations

- v1 is Windows 11 only.
- v1 does not implement per-monitor output files.
- Wake-for-scheduled-captures is best-effort and Windows-dependent.
- Missed scheduled slots are recorded during tray reconciliation; they are not retried automatically.
- Full shutdown is not capturable and is never inferred from image content.
- Mixed-DPI and some protected-content cases should be validated on real hardware.
