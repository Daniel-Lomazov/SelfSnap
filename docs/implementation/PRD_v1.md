# SelfSnap Win11 v1 PRD

## Goal

Deliver a Windows 11 personal utility that captures composite desktop screenshots at configured daily times and stores them locally with honest metadata.

## Must-have behavior

- Manual capture works from CLI and tray.
- Multiple daily schedules are supported.
- A scheduled trigger that does not run because of sleep or unavailability is recorded later as a missed slot.
- Global disable stops scheduled task runs entirely until re-enabled.
- First-run setup must be completed before scheduled capture becomes active.
- Output is local only.
- Tray UI exposes capture now, enable or disable, open folder, open latest, and settings.
- Layered visibility controls are supported:
  - latest status in tray menu
  - failed or missed notifications
  - every-capture notifications
  - on-screen overlay after capture

## Deferred

- Per-monitor outputs
- Rich history UI
- Cross-platform support
- Encryption at rest
- Cloud sync
