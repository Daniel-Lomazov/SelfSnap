# SelfSnap Win11 v1 SRS and Architecture

## Runtime shape

- `SelfSnapTray.exe`: long-running tray agent, scheduler sync, reconcile loop
- `SelfSnapWorker.exe`: one-shot manual or scheduled capture
- Windows Task Scheduler: one daily task per schedule

## Storage contracts

- Config: JSON
- Metadata: SQLite
- Logs: rotating text file
- Images: PNG files in date-based folders

## Outcome taxonomy

- `success/capture_saved`
- `missed/slot_missed_no_attempt`
- `skipped/scheduled_disabled`
- `skipped/scheduled_paused`
- `failed/capture_backend_error`
- `failed/image_write_error`
- `failed/db_write_error`
- `failed/config_invalid`
- `failed/scheduler_sync_error`
- `failed/unexpected_error`
