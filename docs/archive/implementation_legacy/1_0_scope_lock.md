# SelfSnap 1.0 Scope Lock

Last updated: 2026-03-29
Baseline: v0.9.4

This file defines what is locked in and locked out for 1.0.

## Locked IN for 1.0

### Core capture
- Manual capture from tray and CLI
- Scheduled capture with explicit trigger source
- Output formats: PNG, JPEG, WEBP with quality controls
- Composite capture default plus optional per-monitor mode

### Scheduler
- Recurrence units: seconds, minutes, hours, days, weeks, months, years
- Hybrid scheduler: tray-managed high-frequency plus Task Scheduler coarse intervals
- Global enable/disable behavior
- Scheduler sync and reconcile behavior with explicit missed-slot recording

### Storage and retention
- Storage presets: Local Pictures, OneDrive Pictures, Custom Folder
- Date-structured storage paths for captures
- Retention modes: keep forever, archive after days, optional purge after grace period

### UI/runtime surfaces
- First-run setup must complete before scheduled capture activation
- Settings window with schedule editing
- Recent Captures and Statistics windows
- Tray actions for capture, folder access, settings, report issue, update check, reinstall, uninstall, restart, exit

### Trust boundary surfaces
- Privacy warning in README
- Privacy notice in first-run and Settings
- Browser-mediated issue reporting with no automatic screenshot/log/path attachment

### Lifecycle and diagnostics
- Setup/install/reinstall/uninstall/update scripts
- `selfsnap diag` and `selfsnap doctor`
- Logging and issue template support

### Quality baseline
- Windows CI on Python 3.11 and 3.12
- Coverage gate >= 80%
- mypy and ruff clean
- Completed hardware validation checklist before tag

## Locked OUT for 1.0

- Full history browser/search UX
- Encryption at rest implementation
- Cloud sync features
- Cross-platform support
- Enterprise deployment model
- Auto-download and auto-install updates
- Compiled installer (.exe/.msi/MSIX)
- Stealth behavior or telemetry/analytics expansion

## Go / No-Go Gate (verbatim from release criteria)

1. Public docs, implementation docs, sample config, and runtime UI agree on the product contract.
2. The trust boundary is explicit in README, first-run, and Settings.
3. Recurrence and scheduler behavior is stable across the supported date, time, and enable/disable cases.
4. Install, reinstall, uninstall, and update paths succeed on a clean Windows 11 environment.
5. The release pipeline produces reproducible versioned artifacts and release notes.
6. The validation checklist passes on real Windows 11 environments, including multi-monitor and sleep/resume scenarios.
7. Browser-based issue reporting remains safe and does not attach screenshots, logs, or local paths automatically.

## Ship Condition Statement

SelfSnap 1.0.0 is ready to tag when every go/no-go criterion above is satisfied, the hardware validation checklist has recorded evidence on real Windows 11 hardware, CI quality gates remain green, changelog is current, and no out-of-scope feature has been pulled into the release.
