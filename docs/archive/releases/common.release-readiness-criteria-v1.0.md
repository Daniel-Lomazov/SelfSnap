# SelfSnap 1.0 Release Criteria

[ARCHIVED RELEASE]
This file is part of the archived release pack indexed in [README.md](README.md).
It preserves a historical release gate and is not the active product or maintainer contract.

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
- Capture mode supports `composite` output by default and `per_monitor` output when one file per monitor is desired
- Storage presets support local Pictures, OneDrive Pictures, and a custom folder
- Retention supports `keep_forever`, `keep_days`, and optional purge after the grace period
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

## Out of scope for 1.0

- Cross-platform expansion
- Cloud features
- Enterprise management
- Stealth or background-surveillance behavior
- Mandatory encryption-at-rest implementation
- Broad analytics or interpretation features

## Related files

- `README.md`
- `docs/developer/product-requirements-document-v1.md`
- `docs/developer/software-requirements-specification-and-architecture-v1.md`
- `docs/archive/releases/qa.quality-assurance-and-privacy-notes-v1.md`
- `docs/developer/validation-checklist.md`
- [docs/user/config.example.json](../../user/config.example.json)