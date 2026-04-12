# Copilot Instructions for SelfSnap

## Project Overview

SelfSnap is a **Windows 11-only, local-first screenshot utility** (Python 3.11+). It captures composite screenshots of all connected monitors on recurring schedules, stores images locally as PNGs, and records metadata in a local SQLite database. There is no cloud sync or telemetry. The app runs as a system tray process and integrates with Windows Task Scheduler.

## Build, Test, and Lint

```powershell
# Install dev dependencies
python -m pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/unit/test_recurrence.py

# Run a single test by name
pytest tests/unit/test_recurrence.py::test_next_occurrence_daily

# Type checking
mypy src

# Linting + formatting
ruff check .
ruff format .

# Compile check (mirrors CI)
python -m compileall src tests
```

CI runs on Python 3.11 and 3.12 (Windows only) via `.github/workflows/ci.yml`.

## Architecture

### Entry Points

| Command | Module |
|---|---|
| `selfsnap tray` | `selfsnap.tray.app` |
| `selfsnap capture` | `selfsnap.worker` |
| `selfsnap reconcile` | `selfsnap.scheduler.reconcile` |
| `selfsnap sync-scheduler` | `selfsnap.scheduler.task_scheduler` |
| `selfsnap diag` / `doctor` | `selfsnap.cli` |

The CLI dispatcher lives in `cli.py`. Scheduled captures and tray launches each spawn **separate subprocesses** via `runtime_launch.py` — the tray and worker run in isolated processes, not threads.

### Hybrid Scheduler Model

High-frequency schedules (seconds/minutes) are managed by **tray-side polling**. Coarse schedules (hours/days/weeks/months/years) are delegated to **Windows Task Scheduler** via `pywin32`. `scheduler/reconcile.py` handles missed-slot catch-up on app startup.

### Persistence

- **Config:** `%LOCALAPPDATA%\SelfSnap\config\config.json` — loaded/saved by `config_store.py`, deserialized into `AppConfig` dataclass
- **Database:** `%LOCALAPPDATA%\SelfSnap\data\selfsnap.db` — SQLite in WAL mode with busy timeout; schema in `db.py`, record I/O in `records.py`
- **Images:** `%USERPROFILE%\Pictures\SelfSnap\captures\YYYY\MM\DD\` (or OneDrive variant)
- **Logs:** `%LOCALAPPDATA%\SelfSnap\logs\selfsnap.log` — rotating, configured in `logging_setup.py`

All paths resolve through the `AppPaths` dataclass in `paths.py`.

### UI Layer

`tray/` uses `pystray` (tray icon) + `tkinter` (settings/schedule editor windows). The settings window (`tray/settings_window.py`) and schedule editor (`tray/schedule_editor.py`) are the primary UI surfaces.

## Key Conventions

### Models

All core data types are **dataclasses with `slots=True`**:
- Validation via a `.validate()` method that raises `ConfigValidationError`
- Deserialization via `from_dict()` / `from_row()` class methods
- Serialization via `to_dict()` / `to_db_tuple()` instance methods

Enums use `StrEnum` (e.g., `TriggerSource`, `OutcomeCode`, `StoragePreset`).

### Error Handling

Custom exception hierarchy rooted at `SelfSnapError`:
```
SelfSnapError
├── ConfigValidationError
└── CaptureBackendError
```

Exit codes: `0` = OK, `1` = operational failure, `2` = config failure, `3` = scheduler failure, `9` = unexpected error.

### Type Annotations

All functions have full type annotations. `mypy` is configured with `disallow_untyped_defs = true`. Use `from __future__ import annotations` at the top of modules that need forward references.

### Schedule IDs

Schedule identifiers must match `^[a-z0-9_]+$` (lowercase alphanumeric + underscore only).

### Tests

- Unit tests go in `tests/unit/`, integration tests in `tests/integration/`
- Use the `temp_paths` fixture (from `conftest.py`) for any test that needs filesystem or DB access — it provides an isolated `AppPaths` instance rooted in `tmp_path`
- `time-machine` is the approved library for freezing/mocking time in tests
- The pytest cache provider is disabled (`-p no:cacheprovider`); do not rely on it

### Scripts

Dev/install automation lives in `scripts/` as PowerShell `.ps1` files. Use `scripts/setup.ps1` to bootstrap a fresh dev environment. Do not add shell scripts (`.sh`) — Windows PowerShell only.

## Branch Workflow

- Development happens on `dev/lomazov` and lands in `main` through a pull request.
- Avoid direct pushes to `main`; pushes to `dev/lomazov` are expected to drive the automated PR flow.
- Keep PRs merge-ready so repository rulesets and GitHub Copilot review can act on them.
