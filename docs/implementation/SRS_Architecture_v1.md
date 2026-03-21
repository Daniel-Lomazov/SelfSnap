# SelfSnap Win11 v1 SRS and Architecture

## Runtime shape

- `selfsnap tray`: long-running tray agent with first-run setup, scheduler sync, retention housekeeping, and reconcile loop
- `selfsnap capture`: one-shot manual or scheduled capture worker
- Windows Task Scheduler: one daily task per enabled schedule entry

## Storage contracts

- Config, DB, logs, wrapper, and runtime state: `%LOCALAPPDATA%\SelfSnap\`
- Images: `%USERPROFILE%\Pictures\SelfSnap\captures\`
- Archive: `%USERPROFILE%\Pictures\SelfSnap\archive\`

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
