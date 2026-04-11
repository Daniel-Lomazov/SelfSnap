# SelfSnap Win11 SRS and Architecture

## Runtime shape

- `selfsnap tray`: long-running tray agent handling first-run UX, scheduler sync, high-frequency recurrence checks, reconciliation kickoff, and maintenance actions.
- `selfsnap capture`: one-shot worker process for manual and scheduled capture.
- Windows Task Scheduler: one one-shot task per enabled coarse schedule entry (`hours` and above).
- Tray-side runtime scheduler: `seconds` and `minutes` schedules while tray is running.
- Tray `Capture Now` launches capture out-of-process to isolate tray UI state from capture engine side effects.
- Tray `Report Issue` opens a browser-mediated prefilled GitHub issue flow.

## Current operational constraints

- Tray and worker background execution remains console-free.
- Runtime is offline by default.
- Source-based launches are constrained to checkout-local `.venv` interpreter policy.
- Storage presets map to local Pictures, OneDrive Pictures, or user-selected custom roots.
- Settings UI is resizable with responsive card/panel layout transitions.
- Schedule list/editor behavior supports narrow-width stacked mode and wider split mode.
- Reset capture history is destructive, explicit, and user-confirmed.
- Reinstall is non-destructive by default unless cleanup is explicitly requested.

## Trust boundary

- SelfSnap is local-first: no telemetry, no cloud sync, and no silent upload in normal runtime.
- `Report Issue` and `Check for Updates` are explicit user-triggered actions.
- Capture files are not encrypted at rest in current release scope.

## Capture contracts

- Capture output supports `png`, `jpeg`, and `webp` image formats.
- Capture mode supports a composite image by default or one image per monitor in per-monitor mode.

## Storage contracts

- Config, DB, logs, wrapper, and runtime state: `%LOCALAPPDATA%\SelfSnap\`
- Images: `%USERPROFILE%\Pictures\SelfSnap\captures\`
- Archive: `%USERPROFILE%\Pictures\SelfSnap\archive\`

## Storage presets

| Settings label | Config token | Capture root | Archive root |
|---|---|---|---|
| `Local Pictures` | `local_pictures` | `%USERPROFILE%\Pictures\SelfSnap\captures\` | `%USERPROFILE%\Pictures\SelfSnap\archive\` |
| `OneDrive Pictures` | `onedrive_pictures` | `%OneDrive%\Pictures\SelfSnap\captures\` | `%OneDrive%\Pictures\SelfSnap\archive\` |
| `Custom Folder` | `custom` | user-selected | user-selected |

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
- Disabled individual schedules are not registered as active Task Scheduler tasks.
- Scheduler sync failure preserves saved config, marks sync status failed, blocks scheduled capture, and keeps manual capture available.
- Wake-for-scheduled-captures remains optional and best-effort.
- Recurrence anchors are explicit local start date and start time.
- `months` and `years` skip invalid calendar dates rather than rolling forward/backward implicitly.
- Coarse schedules re-register the next one-shot occurrence after each run.

## UI architecture notes

- Fluent styling primitives are centralized in `src/selfsnap/ui/fluent.py`.
- `src/selfsnap/tray/settings_window.py` uses responsive thresholds for stacked/split card layouts.
- Schedule editor/list composition dynamically changes layout based on window width.
- Diagnostics data is summarized in UI-specific presentation helpers under `src/selfsnap/ui/diagnostics.py`.

## Interpreter policy

- Source launches must resolve and use local `.venv` runtime.
- Missing local `.venv` is treated as a setup fault with explicit guidance.
- Foreground and background launch helpers align around the same local interpreter contract.

## Reset semantics

- `Reset Capture History` removes SelfSnap-managed capture files and archive files.
- It clears SQLite history, logs, config, startup shortcut, and scheduled tasks.
- It returns the app to first-run state and relaunches the tray setup flow.
- It does not uninstall wrapper scripts, installed app files, or repo files.
