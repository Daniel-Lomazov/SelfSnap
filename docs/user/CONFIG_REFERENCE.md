# Config Reference

SelfSnap stores its configuration in `%LOCALAPPDATA%\SelfSnap\config\config.json`.

Most users should edit settings through the UI. This reference exists so you can understand what the config stores and how the major keys behave.

## Example File

See [config.example.json](config.example.json) for a complete example.

## Top-Level Keys

| Key | Meaning | Notes |
|---|---|---|
| `schema_version` | config schema version | Current example uses `4` |
| `app_enabled` | master scheduled-capture enable/disable switch | Manual capture remains available even when false |
| `first_run_completed` | whether initial setup has been completed | Controls whether some UI/settings are unlocked |
| `storage_preset` | storage mode | `local_pictures`, `onedrive_pictures`, or `custom` |
| `capture_storage_root` | capture output root | Used directly for saved captures |
| `archive_storage_root` | archive output root | Used for archived capture files |
| `retention_mode` | retention behavior | Example: `keep_forever` |
| `retention_days` | days to keep before moving captures into archive | Required when `retention_mode` is `keep_days` |
| `purge_enabled` | permanently delete archived files after grace period | False means archive-only retention |
| `retention_grace_days` | grace period before purge | Only meaningful when purge is enabled |
| `capture_mode` | capture strategy | `composite` or `per_monitor` |
| `image_format` | saved image format | `png`, `jpeg`, or `webp` |
| `image_quality` | quality value for lossy formats | Relevant for `jpeg` and `webp` |
| `start_tray_on_login` | start tray on login when first run is complete | Install flow also uses this to maintain the startup shortcut |
| `log_level` | runtime log level | Example uses `INFO` |
| `show_last_capture_status` | show latest capture status in the tray menu | Controls menu visibility of recent status information |
| `notify_on_failed_or_missed` | notify on failed or missed captures | UI toggle |
| `notify_on_every_capture` | notify on every scheduled and manual capture | UI toggle |
| `show_capture_overlay` | show a brief post-capture overlay | UI toggle |
| `wake_for_scheduled_captures` | request wake for coarse scheduled captures when supported | Best effort only |
| `scheduler_sync_state` | last scheduler sync state | Internal status surface used by tray and settings |
| `scheduler_sync_message` | extra scheduler status text | Internal status/detail field |
| `settings_window_width` | last stored settings width | UI persistence detail |
| `settings_window_height` | last stored settings height | UI persistence detail |
| `slot_match_tolerance_seconds` | reconciliation tolerance | Internal scheduling behavior |
| `schedules` | recurring schedule list | See schedule object below |
| `extraction_profiles` | stored extraction-profile metadata | Preserved with the config for schema compatibility |

## Storage Presets

| Value | Meaning |
|---|---|
| `local_pictures` | use `%USERPROFILE%\Pictures\SelfSnap` |
| `onedrive_pictures` | use OneDrive Pictures when available |
| `custom` | use the explicitly configured roots |

If the OneDrive preset becomes unavailable later, switch back to `Local Pictures` in Settings and save.

## Retention And Purge

Common combinations:

- `keep_forever` with `purge_enabled = false`: never archive-delete or purge files
- `keep_days` with `retention_days`: captures older than `retention_days` move into archive
- `purge_enabled = true` with `retention_grace_days`: archived files are later removed permanently

`retention_mode` must be exactly `keep_forever` or `keep_days`.

## Capture Output

| Key | Common Values |
|---|---|
| `capture_mode` | `composite`, `per_monitor` |
| `image_format` | `png`, `jpeg`, `webp` |
| `image_quality` | `1` to `100` for lossy output |

`composite` writes one merged image of all displays. `per_monitor` writes one image per display for the same capture slot.

`png` ignores `image_quality`. `jpeg` and `webp` use it.

## Schedule Objects

Each item in `schedules` includes:

| Key | Meaning |
|---|---|
| `schedule_id` | unique identifier for the schedule |
| `label` | human-readable name |
| `enabled` | per-schedule enable/disable flag |
| `interval_value` | recurrence interval value |
| `interval_unit` | recurrence unit: `second`, `minute`, `hour`, `day`, `week`, `month`, or `year` |
| `start_date_local` | local anchor date |
| `start_time_local` | local anchor time |
| `extraction_profile_id` | optional linked extraction profile id | `null` when the schedule has no linked extraction profile |

Schedule identifiers are expected to use lowercase letters, digits, and underscores.

`extraction_profiles` is stored at the top level and preserved across config writes even when the current checkout is not actively editing extraction data.

## Recommended Editing Approach

Prefer the Settings window for normal changes.

Use direct file editing only when you understand the runtime implications and are prepared to validate with:

```powershell
SelfSnap doctor
SelfSnap diag
SelfSnap sync-scheduler
```

## Related Docs

- `INSTALL_AND_UPDATE.md`
- `CLI_REFERENCE.md`
- `TROUBLESHOOTING.md`
- `WORKFLOWS.md`