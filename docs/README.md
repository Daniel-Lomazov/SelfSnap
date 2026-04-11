# Documentation Layout

The documentation is being reorganized on `ui/fluent-compact-tabs` before any future merge into `main`.
Use this index to distinguish current product docs, active release tracking, and historical reference material.

## Start Here

- Top-level `README.md` for end-user-facing product overview, install flow, commands, and release posture.
- Top-level `CHANGELOG.md` for the technical release history.
- `INSTALL_AND_UPDATE.md` for setup, install, update, reinstall, and uninstall guidance.
- `CLI_REFERENCE.md` for the current command-line surface.
- `TROUBLESHOOTING.md` for recovery steps and diagnostics.
- `CONFIG_REFERENCE.md` for config keys and schedule schema.
- `WORKFLOWS.md` for common user flows.
- `implementation/release_progress_tracker.md` for release-doc progress and remaining merge/version blockers.

## Public Product Docs

These are the docs a user should be able to follow without reading source.

- `INSTALL_AND_UPDATE.md`
- `CLI_REFERENCE.md`
- `TROUBLESHOOTING.md`
- `CONFIG_REFERENCE.md`
- `WORKFLOWS.md`

## Active Release Tracking

The documentation and release-readiness program now tracks status in one file:

- `implementation/release_progress_tracker.md`

## Current Implementation Contract

These are the canonical implementation and validation documents for the currently shipped and in-flight product behavior.

- `implementation/PRD_v1.md`
- `implementation/SRS_Architecture_v1.md`
- `implementation/RELEASE_CRITERIA_1_0.md`
- `implementation/QA_Privacy_v1.md`
- `implementation/ISSUE_REPORTING.md`
- `implementation/VALIDATION_CHECKLIST.md`

These focused behavior docs preserve iteration-sensitive implementation context.

- `implementation/UI_PATTERNS_AND_RESPONSIVE_LAYOUT.md`
- `implementation/TRAY_MENU_STRUCTURE_AND_EVOLUTION.md`
- `implementation/INTERPRETER_ENFORCEMENT_AND_VENV_POLICY.md`
- `implementation/SETTINGS_WINDOW_STATE_SYNC_AND_POLLING.md`
- `implementation/SCHEDULER_AND_DST_EDGE_CASES.md`

## Historical Input And Reference

These paths are not the current end-user starting point. They are preserved for product history, design rationale, or future extraction work.

### `archive/customer_baseline/`

Original customer-provided baseline materials that explain how the project scope was formed.

- `archive/customer_baseline/00_README.md`

### `archive/starter_kit/`

Extraction and reuse documents for turning SelfSnap into a repeatable Windows tray app starter.

- `archive/starter_kit/00_README.md`
- `archive/starter_kit/01_Tutorial_First_Derived_App.md`
- `archive/starter_kit/02_How_To_Spin_Up_A_Standard_Tray_App.md`
- `archive/starter_kit/03_Reference_Core_Extraction_Map.md`
- `archive/starter_kit/04_Explanation_Target_Architecture.md`
- `archive/starter_kit/05_Project_Intake_Form.md`
- `archive/starter_kit/06_Starter_Extraction_Plan.md`

### `archive/releases/`

Historical standalone release notes preserved for reference.

- `archive/releases/v0.8.0.md`

### `archive/implementation_legacy/`

Legacy planning and benchmark files preserved for historical traceability.

- `archive/implementation_legacy/README.md`
- `archive/implementation_legacy/1_0_gap_register.md`
- `archive/implementation_legacy/1_0_known_limitations_register.md`
- `archive/implementation_legacy/1_0_planning_decisions.md`
- `archive/implementation_legacy/1_0_scope_lock.md`
- `archive/implementation_legacy/BENCHMARK_1_0_BASELINE.md`
