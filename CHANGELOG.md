# Changelog

## v0.9.4 - 2026-03-25

Why: GitHub-native update check, three CLI lifecycle commands, and three settings window bugs that prevented schedule changes from taking effect.

- **Fix — settings: schedule enabled/disabled change was silently discarded.** `_save_and_close()` iterated `drafts[]` which is only updated when the inline schedule editor "Save" button is clicked. Clicking the main Save without the inline Save discarded the edit — captures kept running unchanged. Fix: `_apply_settings()` now auto-commits the selected schedule's current form state before building `parsed_schedules`.
- **Fix — settings: blank dropdowns on second open (Windows Tkinter multi-root bug).** All `tk.StringVar` / `tk.BooleanVar` were created without `master=root`. After the first `Tk()` is destroyed, the next open's variables bind to a stale default root; readonly comboboxes display blank. Fix: `master=root` added to every variable constructor.
- **Fix — settings: window closed on Save.** The main Save button destroyed the window, preventing users from verifying their changes. Renamed `_save_and_close` → `_apply_settings`; Save now writes to disk and refreshes the schedule tree in-place, then briefly shows `✓ Saved` on the button. The window stays open. "Cancel" renamed "Close".
- **Feat — Check for Updates: GitHub Releases API version check.** Previously ran `git pull --ff-only` unconditionally, which failed on dirty repos or missing credentials. Now fetches the latest release tag from `github.com/repos/…/releases/latest`, compares against the installed version, and skips the update entirely if already current. When a newer release is found, the update uses `git fetch --tags && git reset --hard refs/tags/<tag>` — works regardless of local uncommitted changes.
- **Feat — CLI lifecycle commands.** Three new subcommands for terminal-based management:
  - `selfsnap reinstall [--relaunch-tray]` — offline reinstall from the current source checkout
  - `selfsnap uninstall [--remove-user-data] [--yes]` — prompts for confirmation unless `--yes`
  - `selfsnap update [--check-only] [--relaunch-tray]` — version check + optional update; `--check-only` reports without installing

## v0.9.3 - 2026-03-25

Why: Make lifecycle script launching uniform and robust across all three tray actions.

- **Refactor — uniform lifecycle launch pattern:** All three tray lifecycle actions (Reinstall, Check for Updates, Uninstall) now use the same `run_lifecycle_script_and_check()` path: synchronous execution via `subprocess.run()`, hidden window, I/O to DEVNULL, exit code is the ground truth. The liveness-window approach (`launch_script_and_confirm` / `_wait_for_process_start`) has been removed entirely. It was fundamentally unreliable because any script that completed (success or failure) within the poll window was misread as a launch failure.
- **Fix — Check for Updates:** Was using the liveness-window approach. If `git pull --ff-only` failed quickly (dirty repo, credential issue, no network), the script exited non-zero in < 3s and the tray showed "tray is still running" instead of the real error. Now runs synchronously; non-zero exit shows an actionable error message.
- **Improved error messages:** Reinstall and update failure dialogs now describe the actual failure condition rather than falsely blaming a running tray process.
- **Dead code removed:** `launch_script_and_confirm`, `launch_lifecycle_script`, and `_wait_for_process_start` removed from the codebase.

## v0.9.2 - 2026-03-25

Why: CI infrastructure fixes discovered after pushing v0.9.1.

- **Fix — CI coverage gate:** GUI windows, entry-point stubs, and hardware-dependent modules were included in coverage measurement but can't run headless. Added `[tool.coverage.run]` omit list; coverage after omit is 80.09% (gate passes).
- **Fix — Hypothesis leap-day crash:** `test_iter_occurrences_between_is_monotonically_increasing` used `ref.replace(year=ref.year+2)` which raises `ValueError` when `ref` is Feb 29 and the target year is not a leap year. Fixed using `timedelta` arithmetic.

## v0.9.1 - 2026-03-25

Why: Post-release operational fixes discovered during first use of v0.9.0 on a live install.

- **Fix — reinstall launch failure:** `powershell.exe` launched with `DETACHED_PROCESS` from a windowless `pythonw.exe` parent received no I/O handles and exited within the 2-second confirmation window, causing the tray to falsely report "tray is still running." Added `launch_lifecycle_script()` (no `DETACHED_PROCESS`, I/O to DEVNULL) and `launch_script_and_confirm()` with a 3-second timeout. Added `-WindowStyle Hidden -NonInteractive` to all PowerShell lifecycle invocations.
- **Fix — uninstall launch failure:** `uninstall.ps1` completes in under 3 seconds; a successful exit code was misread as a launch failure by `_wait_for_process_start`. Uninstall now runs synchronously via `run_lifecycle_script_and_check()`; exit code 0 = success, non-zero = failure. Tray exits cleanly on success.
- **Fix — Python path resolution:** `install.ps1` and `reinstall.ps1` now prefer `.venv\Scripts\python.exe` over the Windows Store Python stub. `pythonw.exe` is resolved via `sys.base_prefix` fallback for uv-managed venvs. Bin directory is registered on user PATH automatically.
- **Tray menu — Restart:** Flattened from a submenu to a single button, moved directly above Exit.
- **Tray menu — Reinstall / Check for Updates:** Replaced the Reinstall submenu (From Local Source / From Source and Update) with two flat buttons: `Reinstall` (offline, local source) and `Check for Updates` (git pull + reinstall).
- **Docs:** README and `sample/config.example.json` updated for v0.9.0 features, venv-only setup flow, and new tray menu structure. `schema_version` in example bumped to 3.
- **Git hygiene:** `.github/agents/` and `.github/skills/` unblocked from `.gitignore` and committed; `.hypothesis/` added to ignore list.

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
