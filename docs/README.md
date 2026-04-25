# Documentation Layout

Use this index to distinguish current user docs, current developer docs, and historical reference material.
This documentation set tracks the current preview build and current HEAD behavior, not a stable release manual.

## Navigation hubs

- [../README.md](../README.md): top-level product overview and quick-start hub
- [user/README.md](user/README.md): current user-doc hub
- [developer/README.md](developer/README.md): active maintainer and validation-doc hub
- [archive/README.md](archive/README.md): historical and archived-doc hub

## Start Here

- [../README.md](../README.md) for end-user-facing product overview, install flow, commands, and release posture.
- [../CHANGELOG.md](../CHANGELOG.md) for the technical release history.
- [user/README.md](user/README.md) for the current user docs index.
- [developer/README.md](developer/README.md) for the active developer contract and validation docs index.
- [archive/README.md](archive/README.md) for historical reference packs and retired release material.
- [user/INSTALL_AND_UPDATE.md](user/INSTALL_AND_UPDATE.md) for setup, install, update, reinstall, and uninstall guidance.
- [user/CLI_REFERENCE.md](user/CLI_REFERENCE.md) for the current command-line surface.
- [user/TROUBLESHOOTING.md](user/TROUBLESHOOTING.md) for recovery steps and diagnostics.
- [user/CONFIG_REFERENCE.md](user/CONFIG_REFERENCE.md) for config keys and schedule schema.
- [user/WORKFLOWS.md](user/WORKFLOWS.md) for common user flows.
- [developer/product-requirements-document-v1.md](developer/product-requirements-document-v1.md), [developer/software-requirements-specification-and-architecture-v1.md](developer/software-requirements-specification-and-architecture-v1.md), and [developer/validation-checklist.md](developer/validation-checklist.md) for the active developer contract and release-validation surface.

## Keep These In Sync

- User-entry guidance: [../README.md](../README.md), [user/README.md](user/README.md), [user/INSTALL_AND_UPDATE.md](user/INSTALL_AND_UPDATE.md), and [user/TROUBLESHOOTING.md](user/TROUBLESHOOTING.md)
- Current contract and validation guidance: [developer/README.md](developer/README.md), [developer/product-requirements-document-v1.md](developer/product-requirements-document-v1.md), [developer/software-requirements-specification-and-architecture-v1.md](developer/software-requirements-specification-and-architecture-v1.md), and [developer/validation-checklist.md](developer/validation-checklist.md)
- Archived-material routing: [archive/README.md](archive/README.md) and the relevant archive subfolder README

## Current User Docs

These are the docs a user should be able to follow without reading source.
They now live under `user/`.

- [user/README.md](user/README.md)
- [user/INSTALL_AND_UPDATE.md](user/INSTALL_AND_UPDATE.md)
- [user/CLI_REFERENCE.md](user/CLI_REFERENCE.md)
- [user/TROUBLESHOOTING.md](user/TROUBLESHOOTING.md)
- [user/CONFIG_REFERENCE.md](user/CONFIG_REFERENCE.md)
- [user/WORKFLOWS.md](user/WORKFLOWS.md)

## Current Developer Docs

These are active developer-facing contract and validation docs for the current repo state.
They are not the stable end-user documentation set.

- [developer/README.md](developer/README.md)
- [developer/product-requirements-document-v1.md](developer/product-requirements-document-v1.md)
- [developer/software-requirements-specification-and-architecture-v1.md](developer/software-requirements-specification-and-architecture-v1.md)
- [developer/validation-checklist.md](developer/validation-checklist.md)

## Historical Release Rollout Notes

Completed release-tracking notes are preserved for traceability and should not be treated as active implementation guidance.

- [archive/releases/README.md](archive/releases/README.md)
- [archive/releases/release_history.md](archive/releases/release_history.md)
- [archive/releases/common.release-readiness-criteria-v1.0.md](archive/releases/common.release-readiness-criteria-v1.0.md)
- [archive/releases/policy.local-python-interpreter-enforcement-policy.md](archive/releases/policy.local-python-interpreter-enforcement-policy.md)
- [archive/releases/guide.user-interface-patterns-and-responsive-layout-guidance.md](archive/releases/guide.user-interface-patterns-and-responsive-layout-guidance.md)
- [archive/releases/guide.tray-menu-information-architecture-and-evolution.md](archive/releases/guide.tray-menu-information-architecture-and-evolution.md)
- [archive/releases/qa.quality-assurance-and-privacy-notes-v1.md](archive/releases/qa.quality-assurance-and-privacy-notes-v1.md)
- [archive/releases/qa.scheduler-and-daylight-saving-time-edge-cases.md](archive/releases/qa.scheduler-and-daylight-saving-time-edge-cases.md)

Retired release-specific QA, policy, trust, and internal behavior notes now live under `archive/releases/`.
Former standalone issue-reporting and settings state-sync notes were folded into stable docs and no longer need their own dedicated files.

## Historical Input And Reference

These paths are not the current end-user starting point. They are preserved for product history, design rationale, or future starter-kit and reuse work.

### `archive/customer_baseline/`

Original customer-side intake pack, scope baseline, and handoff notes that explain how the later maintained docs were derived.

- [archive/customer_baseline/README.md](archive/customer_baseline/README.md)

### `archive/starter_kit/`

Archived extraction and reuse pack for turning SelfSnap into a repeatable Windows tray app starter.

- [archive/starter_kit/README.md](archive/starter_kit/README.md)
- [archive/starter_kit/01_Tutorial.md](archive/starter_kit/01_Tutorial.md)
- [archive/starter_kit/02_How_To_Spin_Up.md](archive/starter_kit/02_How_To_Spin_Up.md)
- [archive/starter_kit/03_Extraction_Map.md](archive/starter_kit/03_Extraction_Map.md)
- [archive/starter_kit/04_Target_Architecture.md](archive/starter_kit/04_Target_Architecture.md)
- [archive/starter_kit/05_Project_Intake_Form.md](archive/starter_kit/05_Project_Intake_Form.md)
- [archive/starter_kit/06_Starter_Extraction_Plan.md](archive/starter_kit/06_Starter_Extraction_Plan.md)

### `archive/releases/`

Historical standalone release notes, archived rollout evidence, and retired release-specific validation, policy, guide, and trust docs preserved for reference.

- [archive/releases/README.md](archive/releases/README.md)
- [archive/releases/release_history.md](archive/releases/release_history.md)

### `archive/v1_0_planning_baseline/`

Legacy planning and benchmark files preserved for historical traceability.

- [archive/v1_0_planning_baseline/README.md](archive/v1_0_planning_baseline/README.md)
- [archive/v1_0_planning_baseline/1_0_gap_register.md](archive/v1_0_planning_baseline/1_0_gap_register.md)
- [archive/v1_0_planning_baseline/1_0_known_limitations_register.md](archive/v1_0_planning_baseline/1_0_known_limitations_register.md)
- [archive/v1_0_planning_baseline/1_0_planning_decisions.md](archive/v1_0_planning_baseline/1_0_planning_decisions.md)
- [archive/v1_0_planning_baseline/1_0_scope_lock.md](archive/v1_0_planning_baseline/1_0_scope_lock.md)
- [archive/v1_0_planning_baseline/BENCHMARK_1_0_BASELINE.md](archive/v1_0_planning_baseline/BENCHMARK_1_0_BASELINE.md)
