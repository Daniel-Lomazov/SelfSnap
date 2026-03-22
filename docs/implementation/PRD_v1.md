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

## Current post-v1 fixes

- Background tray and worker operations are console-free.
- Storage presets are explicit choices: `Local Pictures`, `OneDrive`, and `Custom`.
- Reset capture history is a destructive clean-reset action with a permanent warning and returns the app to first-run state.
- Settings window is resizable and fits the visible controls without cropping.
- Reinstall preserves user data and settings by default unless cleanup is requested separately.

## Reset scope

- Removes SelfSnap-managed capture files and archive files
- Clears DB history, logs, and config
- Removes startup shortcut and SelfSnap scheduled tasks
- Relaunches into first-run setup
- Does not uninstall the app or delete repo files

## Deferred

- Per-monitor outputs
- Rich history UI
- Cross-platform support
- Encryption at rest
- Cloud sync
