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
- No cloud sync, telemetry, or stealth behavior

## Privacy warning

SelfSnap stores screenshots locally. Screenshots may contain sensitive information such as messages, credentials, finance pages, or work material. v1 does not encrypt captures at rest. Use only on a machine and storage location you control.

## Quick start

1. Install Python 3.11 or 3.12 on Windows 11.
2. Create a virtual environment.
3. Install the project:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .[dev]
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

## Runtime storage

SelfSnap stores metadata under `%LOCALAPPDATA%\SelfSnap\` by default.

```text
%LOCALAPPDATA%\SelfSnap\
  config\config.json
  data\selfsnap.db
  logs\selfsnap.log
  captures\YYYY\MM\DD\...
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

## Config reference

See `sample/config.example.json` for the full schema.

Important fields:

- `app_enabled`: global enable or disable for scheduled capture
- `pause_until_local`: local ISO datetime string; scheduled runs before this time are skipped
- `capture_storage_root`: output folder for PNG files
- `retention_mode`: `keep_forever` or `keep_days`
- `retention_days`: required only when `retention_mode` is `keep_days`
- `schedules`: list of daily `HH:MM` schedule entries

## Development

```powershell
pytest
ruff check .
mypy src
```

## Packaging

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

The build is prepared to create:

- `SelfSnapTray.exe`
- `SelfSnapWorker.exe`

## Known limitations

- v1 is Windows 11 only.
- v1 does not implement per-monitor output files.
- Missed scheduled slots are recorded during tray reconciliation; they are not retried automatically.
- Full shutdown is not capturable and is never inferred from image content.
- Mixed-DPI and some protected-content cases should be validated on real hardware.
