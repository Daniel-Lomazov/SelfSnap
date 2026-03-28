# Copilot Instructions for SelfSnap

## Project Snapshot

SelfSnap is a Windows 11-only, local-first screenshot utility (Python 3.11+), with tray UI and Task Scheduler integration. It captures monitor screenshots on schedules, stores images locally, and records metadata in local SQLite.

Authoritative product/runtime details live in:
- `README.md`
- `docs/README.md`
- `docs/implementation/SRS_Architecture_v1.md`
- `docs/implementation/PRD_v1.md`
- `docs/implementation/QA_Privacy_v1.md`

Use these docs as references and avoid duplicating long policy text in code changes.

## Build, Test, and Validation

Run from repository root in PowerShell.

```powershell
# Dev install
python -m pip install -e ".[dev]"

# Tests (coverage threshold: 80%)
pytest
pytest tests/unit/test_recurrence.py
pytest tests/unit/test_recurrence.py::test_next_occurrence_daily

# Static checks
mypy src
ruff check .
ruff format .

# Compile guard (CI parity)
python -m compileall src tests

# Pre-commit hooks (ruff check --fix + ruff format)
pre-commit run --all-files
```

CI target is Windows with Python 3.11 and 3.12 (`.github/workflows/ci.yml`).

Files intentionally excluded from coverage (no test coverage required):
- Entry-point stubs: `cli.py`, `__main__.py`, `tray_main.py`, `worker_main.py`
- GUI windows: `tray/settings_window.py`, `tray/first_run.py`, `tray/statistics_window.py`, `tray/recent_captures_window.py`, `tray/report_issue_window.py`
- Hardware-dependent: `capture_engine.py`
- Tray shell: `tray/app.py`, `tray/startup.py`

## Architecture Anchors

Entry points (all dispatched from `selfsnap.cli`):
- `selfsnap tray` → `selfsnap.tray.app`
- `selfsnap capture` → `selfsnap.worker`
- `selfsnap reconcile` → `selfsnap.scheduler.reconcile`
- `selfsnap sync-scheduler` → `selfsnap.scheduler.task_scheduler`
- `selfsnap reinstall` / `selfsnap uninstall` / `selfsnap update` → `selfsnap.lifecycle_actions`
- `selfsnap diag` / `selfsnap doctor` → `selfsnap.cli`

Worker exit codes (defined as constants in `worker.py`):
- `EXIT_OK = 0`
- `EXIT_OPERATIONAL_FAILURE = 1`
- `EXIT_CONFIG_FAILURE = 2`
- `EXIT_SCHEDULER_FAILURE = 3`
- `EXIT_UNEXPECTED = 9`

Core runtime boundaries:
- Tray and capture worker run in separate subprocesses (`runtime_launch.py`), not threads.
- Hybrid scheduling model:
	- Fine-grained (`seconds`, `minutes`) handled in tray polling.
	- Coarse-grained (`hours` and above) delegated to Windows Task Scheduler via `pywin32`.
	- `scheduler/backends.py` defines the `TaskSchedulerBackend` Protocol for swapping implementations in tests.
- Missed-slot catch-up is handled by reconcile logic on startup.

Persistence paths are resolved through `AppPaths` in `paths.py`:
- Config and app data: `%LOCALAPPDATA%\SelfSnap\...`
- Captures/archive: Pictures or OneDrive-backed pictures roots

## Coding Conventions

Data model conventions:
- Prefer dataclasses with `slots=True` for core models.
- Keep `validate()`, `from_dict()/from_row()`, `to_dict()/to_db_tuple()` patterns consistent.
- Prefer `StrEnum` for string-backed enums.
- `AppConfig.from_dict()` handles schema migrations from v1/v2 → v3 (`SCHEMA_VERSION = 3` in `models.py`); preserve migration logic when modifying config deserialization.

Typing and errors:
- Full type annotations are expected (`mypy` strict settings include `disallow_untyped_defs = true`).
- Keep exception usage aligned with project hierarchy rooted at `SelfSnapError`.
- Preserve CLI exit code behavior and avoid changing semantics unless explicitly requested.

Scheduling and IDs:
- Schedule IDs must match `^[a-z0-9_]+$`.
- Preserve recurrence semantics, especially month/year invalid-date skip behavior.

## Testing Conventions

- Unit tests in `tests/unit/`; integration tests in `tests/integration/`.
- Use `temp_paths` fixture for filesystem/database isolation.
- Use `time-machine` for time-sensitive recurrence tests.
- Use `hypothesis` for property-based recurrence edge cases (see `test_recurrence_hypothesis.py`).
- Do not rely on pytest cache provider (disabled in config).
- For behavior changes, add or update focused tests in the nearest relevant test module.

## Windows and Script Rules

- This project is Windows-first; prefer PowerShell commands and scripts.
- Use existing scripts in `scripts/` for setup/install/reinstall/uninstall/smoke-test flows.
- Do not introduce `.sh` automation scripts for repo workflows unless explicitly requested.

## Edit Guidelines for Agents

- Make minimal, targeted changes; do not reformat unrelated code.
- Preserve existing architecture and module boundaries.
- Link to docs instead of embedding large documentation blocks in code comments or new files.
- If a change touches scheduler, capture, storage, or privacy-sensitive behavior, validate with tests and mention what was run.
