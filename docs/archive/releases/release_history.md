# Historical Release Notes And Evidence

[ARCHIVED RELEASE]
This file is part of the archived release pack indexed in [README.md](README.md).
It preserves historical release evidence and is not the active product or maintainer contract.

This file consolidates archived release notes and rollout evidence that are no longer part of the active documentation path.
Use `docs/README.md` for current user and implementation guidance.

## v1.1.0 Documentation Rollout Record

This section preserves the completed documentation and release-sequencing work for `v1.1.0`.
It is historical release evidence, not an active tracker.

### Objective At The Time

Complete the documentation overhaul for the v1.1.0 UI/runtime refresh before the release landed on `main`.

### Final Status

- Public docs rewrite: complete
- Temporary working docs refresh: complete
- New internal behavior docs: complete
- Archive/reclassification pass: complete
- Version surface synchronization: complete (`v1.1.0`)
- Final merge/tag sequencing: complete

### Completed Deliverables

- Public docs:
  - `docs/product/INSTALL_AND_UPDATE.md`
  - `docs/product/CLI_REFERENCE.md`
  - `docs/product/TROUBLESHOOTING.md`
  - `docs/product/CONFIG_REFERENCE.md`
  - `docs/product/WORKFLOWS.md`
- Maintainer contract docs retained:
  - `docs/maintainer/product-requirements-document-v1.md`
  - `docs/maintainer/software-requirements-specification-and-architecture-v1.md`
  - `docs/archive/releases/common.release-readiness-criteria-v1.0.md`
  - `docs/archive/releases/qa.quality-assurance-and-privacy-notes-v1.md`
  - `docs/maintainer/validation-checklist.md`
  - issue-reporting privacy-boundary guidance, later folded into `README.md` and `docs/product/TROUBLESHOOTING.md`
- New internal behavior docs:
  - `docs/archive/releases/guide.user-interface-patterns-and-responsive-layout-guidance.md`
  - `docs/archive/releases/guide.tray-menu-information-architecture-and-evolution.md`
  - `docs/archive/releases/policy.local-python-interpreter-enforcement-policy.md`
  - settings state-sync regression guidance, later folded into `docs/maintainer/software-requirements-specification-and-architecture-v1.md` and `docs/maintainer/validation-checklist.md`
  - `docs/archive/releases/qa.scheduler-and-daylight-saving-time-edge-cases.md`

### Release Outcome

`v1.1.0` was released with the documentation, versioning, and merge/tag sequencing work completed.

### Historical Release-Readiness Checks

Before the `v1.1.0` release, the following UI/runtime documentation checks had to be closed:

1. Fluent-style Settings behavior is documented and validated for narrow and wide layouts.
2. Schedule list/editor reflow and column autofit behavior is validated against recent regressions.
3. Tray menu hierarchy and wording are reflected accurately in public docs and troubleshooting docs.
4. Local `.venv` interpreter enforcement behavior is documented and validated for both valid and missing-venv scenarios.
5. State-sync protections for scheduled-capture enable/disable toggles are validated against external config polling.
6. Diagnostics and issue-reporting flows remain user-controlled and privacy-safe.

## v1.0.0 Validation Evidence - 2026-03-29

This section preserves the dated execution evidence that used to live at the bottom of `docs/maintainer/validation-checklist.md`.

### Environment Snapshot

- Date: 2026-03-29
- Host: Windows 11 (user workstation)
- Python: 3.12.11 (`.venv\Scripts\python.exe`)
- App version from `selfsnap diag`: `0.9.4`

### Completed Checks

- `selfsnap doctor` returned `ok: true` with successful imports for `pystray`, `PIL`, and `mss`.
- `selfsnap diag` confirmed resolved paths, scheduler sync state `ok`, and a latest `capture_saved` record with `file_present: true`.
- Manual capture completed successfully and wrote a capture file under `Pictures\SelfSnap\captures\2026\03\29\`.
- A temporary coarse `hour` schedule was registered, verified in Task Scheduler, and then cleaned up.
- Full automated functional gate passed during Phase C prep: `pytest -q` -> `134 passed`, coverage `80.46%`.

### Notes At The Time

- Minute-level schedules did not appear in `schtasks /Query`, which was expected because minute schedules are tray-managed high-frequency behavior.
- Remaining manual verification at the time focused on tray UI, issue-report flow, forced failure paths, lifecycle actions, and logon startup behavior.

### Post-Release Confirmation

- `selfsnap diag` reported `app_version: "1.0.0"` in the latest record.
- `selfsnap diag` reported `scheduler_sync_state: "ok"`.
- At least one coarse scheduled task was present in `Ready` state.
- Runtime dependency probe remained healthy.

## v0.8.0 Release Notes

`v0.8.0` turned scheduling into a real recurring system instead of a single daily-time model. The app could now express fast repeating captures, coarse recurring captures, and a clearer editing workflow in Settings.

### What Changed

- Schedules could be added as `Every N seconds`, `minutes`, `hours`, `days`, `weeks`, `months`, or `years`.
- Each schedule became anchored to a specific start date and start time in local time.
- Settings gained a structured schedule editor with `Add`, `Save`, `Cancel`, and `Delete`.
- Existing daily schedules were migrated into the new recurrence model automatically.

### Important Behavior

- `seconds` and `minutes` schedules require the tray to be running in the logged-in session.
- `months` and `years` skip invalid dates instead of moving to the last day of the period.
- The schedule-model migration changed schedule representation, not existing stored captures or capture history.

### Read More

- Technical implementation details: [`CHANGELOG.md`](../../CHANGELOG.md)
- Repository overview: [`README.md`](../../README.md)