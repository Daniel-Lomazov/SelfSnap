# SelfSnap Win11 v1 SRS and Architecture

## Runtime shape

- `selfsnap tray`: long-running tray agent with first-run setup, scheduler sync, retention housekeeping, and reconcile loop
- `selfsnap capture`: one-shot manual or scheduled capture worker
- Windows Task Scheduler: one daily task per enabled schedule entry
- Tray `Capture Now` launches the one-shot capture worker out of process so capture-side DPI or monitor state cannot mutate tray UI geometry.

## Current operational constraints

- Tray and worker background execution does not open a visible console window.
- Storage presets map to local Pictures, OneDrive Pictures, or a custom path.
- Reset capture history is a deliberate destructive operation with explicit user confirmation.
- Settings UI supports resizing and content-aware layout, but it does not auto-persist incidental geometry changes from capture activity.
- Reinstall is non-destructive by default and preserves user data and configuration unless cleanup is requested separately.
- A separate elevated cleanup script removes stale ACL-poisoned pytest folders when needed.

## Storage contracts

- Config, DB, logs, wrapper, and runtime state: `%LOCALAPPDATA%\SelfSnap\`
- Images: `%USERPROFILE%\Pictures\SelfSnap\captures\`
- Archive: `%USERPROFILE%\Pictures\SelfSnap\archive\`

## Storage presets

| Settings label | Config token | Capture root | Archive root |
|---|---|---|---|
| `Local Pictures` | `local_pictures` | `%USERPROFILE%\Pictures\SelfSnap\captures\` | `%USERPROFILE%\Pictures\SelfSnap\archive\` |
| `OneDrive` | `onedrive_pictures` | `%OneDrive%\Pictures\SelfSnap\captures\` | `%OneDrive%\Pictures\SelfSnap\archive\` |
| `Custom` | `custom` | user-selected | user-selected |

If `%OneDrive%` is unavailable, resolution falls back to `%USERPROFILE%\OneDrive\Pictures\SelfSnap\...`. The preset is rejected unless the resolved OneDrive base path exists and is writable.

## Outcome taxonomy

- `success/capture_saved`
- `missed/slot_missed_no_attempt`
- `skipped/scheduled_disabled` as a defensive outcome only if a stale scheduled trigger still fires
- `failed/capture_backend_error`
- `failed/image_write_error`
- `failed/db_write_error`
- `failed/config_invalid`
- `failed/scheduler_sync_error`
- `failed/unexpected_error`

## Scheduler semantics

- Global disable removes all SelfSnap scheduled capture tasks.
- Individual disabled schedules are not kept active in Task Scheduler.
- A scheduler sync failure leaves config saved, marks sync state failed, blocks scheduled capture, and keeps manual capture available.
- Wake-for-scheduled-captures is an optional best-effort setting, default OFF.

## Reset semantics

- `Reset Capture History` removes SelfSnap-managed capture files and archive files.
- It clears SQLite history, logs, config, startup shortcut, and scheduled tasks.
- It returns the app to first-run state and relaunches the tray setup flow.
- It does not uninstall wrapper scripts, installed app files, or repo files.
