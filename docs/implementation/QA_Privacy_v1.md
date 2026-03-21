# SelfSnap Win11 v1 QA and Privacy Notes

## Privacy

- No cloud sync or remote upload
- No stealth mode
- Tray must remain visible while active
- Logs must not include image contents or inferred activity
- User-visible indicators are layered and independently togglable

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
