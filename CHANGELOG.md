# Changelog

## v0.9.0 - 2026-03-25

Why: Four investment areas advance SelfSnap toward v1.0: true permanent retention, capture quality controls, in-tray observability, and developer experience hardening.

- **True Permanent Retention (E1.1):** `retention.py` gains a second purge pass (`apply_purge`) that permanently deletes archived files after a configurable grace period (default 30 days). `purge_enabled` and `retention_grace_days` added to `AppConfig` (schema v3). `CaptureRecord` gains `purged_utc` timestamp. Settings UI shows grace-period spinner.
- **Capture Quality Controls (E2.1, E2.2):** `capture_engine.py` supports both composite and per-monitor capture modes. `CaptureImage` returns a list of images. `image_format` (png/jpeg/webp) and `image_quality` (1–100) are configurable via Settings. `worker.py` and test fixtures updated.
- **History & Observability (E3.1, E3.2, E3.3):** New `recent_captures_window.py` shows a thumbnail quick-view of the last 10 captures with timestamps and trigger tooltips. New `statistics_window.py` shows totals, storage used, outcome counts, and a 30-day Canvas bar chart. Both are accessible from the tray menu. Schedule editor shows per-schedule run history (last 5 outcomes).
- **Developer Experience (E1.3, E1.4, E4.1, E4.2):** pytest-cov gate at 80% line coverage. `.pre-commit-config.yaml` with ruff + mypy hooks. `hypothesis` property-based tests for recurrence semantics. `TaskSchedulerBackend` protocol with `InMemoryTaskSchedulerBackend` decouples scheduler tests from live Windows Task Scheduler.
- **Docs:** `.github/copilot-instructions.md` added for Copilot context continuity.

## v0.8.0 - 2026-03-23

Why: The recurring schedule overhaul replaced the old daily-time model with a broader recurrence system and the runtime needed to execute it safely.

- Replaced the daily-only schedule shape with a recurrence schema that stores `interval_value`, `interval_unit`, `start_date_local`, and `start_time_local`.
- Added support for recurring schedules in `seconds`, `minutes`, `hours`, `days`, `weeks`, `months`, and `years`, with anchored local start date/time semantics.
- Added automatic migration of legacy daily schedules into `every 1 day` recurrence entries.
- Split scheduling into a hybrid runtime model:
  - tray-managed `seconds` and `minutes`
  - Windows Task Scheduler-backed `hours`, `days`, `weeks`, `months`, and `years`
- Changed coarse scheduling from fixed daily tasks to one-shot next-occurrence task registration.
- Reworked the Settings schedule UI into a structured editor with `Add`, `Save`, `Cancel`, `Delete`, single-select editing, and multi-select delete-only behavior.
- Updated missed-slot reconciliation to iterate recurrence-aware coarse occurrences instead of daily wall-clock slots.
- Hardened concurrent capture handling with collision-safe same-second output naming and SQLite busy-timeout/WAL behavior.
- Expanded README, in-app help, and automated coverage around recurrence semantics, migration, scheduler behavior, and schedule editing.

## v0.7.0 - 2026-03-23

Why: The current public-ready branch reached a stable offline-first runtime and reviewable release posture.

- Hardened the tray runtime around offline-by-default behavior, lifecycle actions, and browser-only issue reporting.
- Tightened Settings and First Run UI labels, sizing, and tray dialog behavior for public-facing use.
- Aligned public docs and workflow wording with the actual runtime boundary and release posture.

## v0.6.0 - 2026-03-23

Why: SelfSnap gained an integrated feedback path and repository-side issue intake automation.

- Added tray-driven issue reporting with safe diagnostics and a dedicated report dialog.
- Added GitHub issue templates and CI/intake workflows to keep the repo reviewable.
- Expanded tests and documentation around issue reporting behavior and repo hygiene.

## v0.5.0 - 2026-03-23

Why: Repository hygiene, install behavior, and pytest cleanup became stable enough for repeated maintenance.

- Hardened install and uninstall tooling and added dedicated cleanup support for stale pytest artifacts.
- Tightened repo hygiene, ignore rules, and documentation around validation leftovers.
- Anchored pytest cleanup logic to the repo root and added stronger verification coverage.

## v0.4.0 - 2026-03-23

Why: The first broad post-v1 stabilization pass closed the most disruptive product and UI regressions.

- Finalized the post-v1 fixes across storage presets, reset behavior, tray state, and runtime launch paths.
- Isolated tray UI state more safely and hardened uninstall fallback behavior.
- Stabilized the settings window after capture-related regressions and expanded UI regression coverage.

## v0.3.0 - 2026-03-22

Why: Source setup and runtime verification became reliable enough for repeated local installs.

- Added a bootstrap setup script for creating a clean development or runtime environment.
- Hardened runtime dependency detection so broken Pillow/runtime states fail clearly.
- Added targeted tests around runtime verification and setup-related behavior.

## v0.2.0 - 2026-03-22

Why: Windows runtime and installation flow became usable end to end.

- Finalized Windows runtime, tray startup, worker packaging readiness, and scheduler integration.
- Aligned documentation with the Windows install and validation flow.
- Expanded automated coverage around archive behavior and scheduler-backed paths.

## v0.1.0 - 2026-03-21

Why: First tested runnable SelfSnap baseline.

- Initial Windows 11 tray app with manual and scheduled screenshot capture.
- Local SQLite metadata, retention handling, and tray control surface.
- Baseline automated coverage for config, retention, and worker flows.
