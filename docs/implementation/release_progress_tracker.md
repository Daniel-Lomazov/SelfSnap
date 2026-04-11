# Release Documentation Progress Tracker

## Objective

Complete the documentation overhaul for `ui/fluent-compact-tabs` before any merge into `main`.

## Progress summary

- Public docs rewrite: complete
- Canonical implementation docs refresh: complete
- New internal behavior docs: complete
- Archive/reclassification pass: complete
- Version surface synchronization: pending decision
- Final merge/tag sequencing: pending decision

## Completed deliverables

- Public docs:
  - `docs/INSTALL_AND_UPDATE.md`
  - `docs/CLI_REFERENCE.md`
  - `docs/TROUBLESHOOTING.md`
  - `docs/CONFIG_REFERENCE.md`
  - `docs/WORKFLOWS.md`
- Canonical implementation docs refreshed:
  - `docs/implementation/PRD_v1.md`
  - `docs/implementation/SRS_Architecture_v1.md`
  - `docs/implementation/RELEASE_CRITERIA_1_0.md`
  - `docs/implementation/QA_Privacy_v1.md`
  - `docs/implementation/VALIDATION_CHECKLIST.md`
  - `docs/implementation/ISSUE_REPORTING.md`
- New internal behavior docs:
  - `docs/implementation/UI_PATTERNS_AND_RESPONSIVE_LAYOUT.md`
  - `docs/implementation/TRAY_MENU_STRUCTURE_AND_EVOLUTION.md`
  - `docs/implementation/INTERPRETER_ENFORCEMENT_AND_VENV_POLICY.md`
  - `docs/implementation/SETTINGS_WINDOW_STATE_SYNC_AND_POLLING.md`
  - `docs/implementation/SCHEDULER_AND_DST_EDGE_CASES.md`

## Remaining release blockers

1. Choose target release version for the UI branch integration.
2. Synchronize all version surfaces (`pyproject.toml`, `src/selfsnap/version.py`, `README.md`, `CHANGELOG.md`).
3. Finalize merge and tag runbook when version is locked.
