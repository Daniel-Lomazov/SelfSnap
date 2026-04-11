# SelfSnap 1.0 Release Criteria

## Purpose

This document defines what `1.0.0` means for SelfSnap as a public release.
The target is a trustworthy Windows 11 release for privacy-minded power users, not a broad consumer or enterprise launch.

## 1.0 audience

- Windows 11 users who want local scheduled screenshot capture with transparent controls
- Users who are comfortable with an intentional, narrow desktop utility rather than a full productivity platform
- Users who value privacy boundaries more than cloud features or passive analytics

## Hard product invariants

- Windows 11 only
- Logged-in desktop session only
- Local-first operation
- No telemetry
- No cloud sync
- No stealth behavior
- Browser-mediated issue reporting only
- v1 does not encrypt captures at rest

## Supported 1.0 contract

- Manual capture works from the tray and CLI
- Recurring schedules support `seconds`, `minutes`, `hours`, `days`, `weeks`, `months`, and `years`
- High-frequency schedules are tray-managed and coarse schedules are Task Scheduler-backed
- Capture output supports `png`, `jpeg`, and `webp`
- Capture mode supports composite output by default and optional per-monitor output
- Storage presets support local Pictures, OneDrive Pictures, and a custom folder
- Retention supports keep forever, archive-after-days, and optional purge-after-grace-period
- Recent captures and statistics windows provide lightweight review and status confirmation
- Install, reinstall, uninstall, and update flows preserve user trust and user control

## Known 1.0 limitations

- No encryption at rest
- No cross-platform support
- No cloud sync or remote backup
- No enterprise deployment model
- No guarantee of capture from full shutdown
- Wake-from-sleep is best effort only
- No full history browser or search-oriented review UI

## Go / no-go gate

SelfSnap should not ship as `1.0.0` until all of the following are true:

1. Public docs, implementation docs, sample config, and runtime UI agree on the product contract.
2. The trust boundary is explicit in README, first-run, and Settings.
3. Recurrence and scheduler behavior is stable across the supported date, time, and enable/disable cases.
4. Install, reinstall, uninstall, and update paths succeed on a clean Windows 11 environment.
5. The release pipeline produces reproducible versioned artifacts and release notes.
6. The validation checklist passes on real Windows 11 environments, including multi-monitor and sleep/resume scenarios.
7. Browser-based issue reporting remains safe and does not attach screenshots, logs, or local paths automatically.

## Current branch merge-release readiness addendum

The UI branch introduces material UX/runtime changes beyond the original 1.0 baseline.
Before merging `ui/fluent-compact-tabs` into `main`, all of the following branch-specific checks must be closed:

1. Fluent-style Settings behavior is documented and validated for narrow and wide layouts.
2. Schedule list/editor reflow and column autofit behavior is validated against recent regressions.
3. Tray menu hierarchy and wording are reflected accurately in public docs and troubleshooting docs.
4. Local `.venv` interpreter enforcement behavior is documented and validated for both valid and missing-venv scenarios.
5. State-sync protections for scheduled-capture enable/disable toggles are validated against external config polling.
6. Diagnostics and issue-reporting flows remain user-controlled and privacy-safe.

## Out of scope for 1.0

- Cross-platform expansion
- Cloud features
- Enterprise management
- Stealth or background-surveillance behavior
- Mandatory encryption-at-rest implementation
- Broad analytics or interpretation features

## Related files

- `README.md`
- `docs/implementation/PRD_v1.md`
- `docs/implementation/SRS_Architecture_v1.md`
- `docs/implementation/QA_Privacy_v1.md`
- `docs/implementation/VALIDATION_CHECKLIST.md`
- `sample/config.example.json`