# SelfSnap Win11 v1 QA and Privacy Notes

## Privacy

- No cloud sync or remote upload
- No stealth mode
- v1 does not encrypt captures at rest
- Tray must remain visible while active
- Logs must not include image contents or inferred activity
- User-visible indicators are layered and independently togglable
- No automatic outbound network traffic during normal runtime
- Only explicit browser-open feedback and explicit source-update reinstall may touch the network

## Current privacy and control notes

- Background actions stay console-free and do not flash a command window
- Source-based runtime launch paths enforce checkout-local `.venv` interpreter usage
- Reset capture history shows a permanent warning before deletion
- Reset removes SelfSnap-managed capture/archive files, DB state, logs, config, startup shortcut, and scheduled tasks, then relaunches first run
- Reinstall defaults preserve user data unless the user explicitly opts into cleanup
- Tray `Report Issue` shares only a short user description plus optional safe diagnostics
- Screenshots, screenshot contents, logs, DB contents, and local storage paths are never attached automatically to issue reports
- Issue reporting is browser-mediated only; the app does not create GitHub issues directly
- Stale ACL-poisoned pytest folders are cleaned with a dedicated elevated script, not by normal app flow
- First-run and Settings must state plainly that captures are local-only and unencrypted at rest in v1

## Current UI branch QA focus

- Responsive Settings layout transitions remain readable and stable during width changes
- Schedule list/editor behavior remains usable in stacked and split modes
- External config polling does not overwrite unsaved local changes to scheduled-capture enable state
- Diagnostics card summaries update correctly as local state changes
- Tray menu actions map to the documented support and lifecycle behavior

## Manual QA focus

- Mixed monitor layouts
- Locked-session capture behavior
- Sleep through a schedule then reconcile within about one minute of tray startup or resume
- Disabled schedules producing no run at all
- Retention archive moves and metadata updates
- Source-based install and uninstall under a standard user account

## Visibility defaults

- Latest status in tray menu: ON
- Failed or missed notifications: ON
- Every-capture notifications: OFF
- On-screen overlay: OFF
