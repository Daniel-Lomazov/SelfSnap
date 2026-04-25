# Documentation Layout

Use this index to distinguish current product docs, current maintainer docs, and historical reference material.

## Start Here

- Top-level `README.md` for end-user-facing product overview, install flow, commands, and release posture.
- Top-level `CHANGELOG.md` for the technical release history.
- `product/README.md` for the current end-user docs index.
- `maintainer/README.md` for the active maintainer contract and validation docs index.
- `archive/README.md` for historical reference packs and retired release material.
- `product/INSTALL_AND_UPDATE.md` for setup, install, update, reinstall, and uninstall guidance.
- `product/CLI_REFERENCE.md` for the current command-line surface.
- `product/TROUBLESHOOTING.md` for recovery steps and diagnostics.
- `product/CONFIG_REFERENCE.md` for config keys and schedule schema.
- `product/WORKFLOWS.md` for common user flows.
- `maintainer/product-requirements-document-v1.md`, `maintainer/software-requirements-specification-and-architecture-v1.md`, and `maintainer/validation-checklist.md` for the active maintainer contract and release-validation surface.

## Current Product Docs

These are the docs a user should be able to follow without reading source.
They now live under `product/`.

- `product/README.md`
- `product/INSTALL_AND_UPDATE.md`
- `product/CLI_REFERENCE.md`
- `product/TROUBLESHOOTING.md`
- `product/CONFIG_REFERENCE.md`
- `product/WORKFLOWS.md`

## Current Maintainer Docs

These are active maintainer-facing contract and validation docs for the current repo state.
They are not the stable end-user documentation set.

- `maintainer/README.md`
- `maintainer/product-requirements-document-v1.md`
- `maintainer/software-requirements-specification-and-architecture-v1.md`
- `maintainer/validation-checklist.md`

## Historical Release Rollout Notes

Completed release-tracking notes are preserved for traceability and should not be treated as active implementation guidance.

- `archive/releases/README.md`
- `archive/releases/release_history.md`
- `archive/releases/common.release-readiness-criteria-v1.0.md`
- `archive/releases/policy.local-python-interpreter-enforcement-policy.md`
- `archive/releases/guide.user-interface-patterns-and-responsive-layout-guidance.md`
- `archive/releases/guide.tray-menu-information-architecture-and-evolution.md`
- `archive/releases/qa.quality-assurance-and-privacy-notes-v1.md`
- `archive/releases/qa.scheduler-and-daylight-saving-time-edge-cases.md`

Retired release-specific QA, policy, trust, and internal behavior notes now live under `archive/releases/`.
Former standalone issue-reporting and settings state-sync notes were folded into stable docs and no longer need their own dedicated files.

## Historical Input And Reference

These paths are not the current end-user starting point. They are preserved for product history, design rationale, or future starter-kit and reuse work.

### `archive/customer_baseline/`

Original customer-side intake pack, scope baseline, and handoff notes that explain how the later maintained docs were derived.

- `archive/customer_baseline/README.md`

### `archive/starter_kit/`

Archived extraction and reuse pack for turning SelfSnap into a repeatable Windows tray app starter.

- `archive/starter_kit/README.md`
- `archive/starter_kit/01_Tutorial.md`
- `archive/starter_kit/02_How_To_Spin_Up.md`
- `archive/starter_kit/03_Extraction_Map.md`
- `archive/starter_kit/04_Target_Architecture.md`
- `archive/starter_kit/05_Project_Intake_Form.md`
- `archive/starter_kit/06_Starter_Extraction_Plan.md`

### `archive/releases/`

Historical standalone release notes, archived rollout evidence, and retired release-specific validation, policy, guide, and trust docs preserved for reference.

- `archive/releases/README.md`
- `archive/releases/release_history.md`

### `archive/v1_0_planning_baseline/`

Legacy planning and benchmark files preserved for historical traceability.

- `archive/v1_0_planning_baseline/README.md`
- `archive/v1_0_planning_baseline/1_0_gap_register.md`
- `archive/v1_0_planning_baseline/1_0_known_limitations_register.md`
- `archive/v1_0_planning_baseline/1_0_planning_decisions.md`
- `archive/v1_0_planning_baseline/1_0_scope_lock.md`
- `archive/v1_0_planning_baseline/BENCHMARK_1_0_BASELINE.md`
