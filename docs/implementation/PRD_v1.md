# SelfSnap Win11 v1 PRD

## Goal

Deliver a Windows 11 personal utility that captures desktop screenshots on recurring schedules and stores them locally with honest metadata.

## Must-have behavior

- Manual capture works from CLI and tray.
- Recurring schedules are supported for seconds, minutes, hours, days, weeks, months, and years.
- A scheduled trigger that does not run because of sleep or unavailability is recorded later as a missed slot.
- Global disable stops scheduled task runs entirely until re-enabled.
- First-run setup must be completed before scheduled capture becomes active.
- Output is local only.
- Capture output supports composite mode by default and optional per-monitor output.
- Image output supports `png`, `jpeg`, and `webp`, with quality control for `jpeg` and `webp`.
- Tray UI exposes capture now, enable or disable, open folder, open latest, and settings.
- Layered visibility controls are supported:
  - latest status in tray menu
  - failed or missed notifications
  - every-capture notifications
  - on-screen overlay after capture

## Current shipped scope additions

- Background tray and worker operations are console-free.
- Storage presets are explicit choices: `Local Pictures`, `OneDrive Pictures`, and `Custom Folder`.
- Reset capture history is a destructive clean-reset action with a permanent warning and returns the app to first-run state.
- Settings window is resizable and opens at a stable minimum size so capture activity does not perturb its geometry.
- Tray issue reporting opens a browser-prepared GitHub issue without attaching screenshots automatically.
- Recent captures and statistics windows provide lightweight in-tray review without requiring a full history browser.
- Capture mode and image format are configurable from Settings.
- Reinstall preserves user data and settings by default unless cleanup is requested separately.
- A dedicated elevated cleanup script is available for stale ACL-poisoned pytest folders from older runs.
- Schedule editing uses a structured builder with `Add`, `Save`, `Cancel`, `Delete`, and multi-select delete-only behavior.
- Recurrence anchors are explicit local start date and start time values.

## Reset scope

- Removes SelfSnap-managed capture files and archive files
- Clears DB history, logs, and config
- Removes startup shortcut and SelfSnap scheduled tasks
- Relaunches into first-run setup
- Does not uninstall the app or delete repo files

## Deferred

- Full history browser and search-focused review UX
- Cross-platform support
- Encryption at rest
- Cloud sync
