# Workflows

This document walks through the most common SelfSnap flows using the current tray and Settings UI.

## 1. First Run And First Capture

1. Run `scripts/user/setup.ps1` from the repository root.
2. Run `scripts/user/install.ps1`.
3. Start the app with `SelfSnap tray` if it is not already running.
4. Open Settings from the tray.
5. Review storage, notifications, and privacy-related options.
6. Use `Capture Now` to launch a manual capture.
7. Check the latest capture status in the tray or Settings.

## 2. Add A Recurring Schedule

1. Open Settings.
2. Go to `Schedules`.
3. In `Editor`, enter a label, interval value, interval unit, start date, and start time.
4. Click `Add`.
5. Confirm the new schedule appears in `Configured captures`.
6. Click the main `Save` button for the Settings window.
7. If needed, run `SelfSnap sync-scheduler` after saving.

Notes:

- clicking the `Status` column in the schedule list pauses or resumes an individual schedule,
- the `Recent runs` panel updates for the currently selected schedule.

## 3. Pause Or Resume Scheduled Captures

Use either path:

### Tray path

1. Open the tray menu.
2. Choose `Pause Scheduled Captures` or `Resume Scheduled Captures`.

### Settings path

1. Open Settings.
2. Toggle `Scheduled captures enabled`.
3. Click `Save`.

The Settings window is designed to reflect external tray changes while still preserving your unsaved local toggle until you save or close.

## 4. Change Storage Preset Or Recover From A OneDrive Problem

1. Open Settings.
2. Go to `Storage`.
3. Choose a storage preset or browse for custom roots.
4. Review retention, format, and purge behavior.
5. Save.
6. Run a manual capture to verify the new location.

If OneDrive storage becomes unavailable, switch back to `Local Pictures`, save, and verify with `SelfSnap diag`.

## 5. Use Diagnostics And Report An Issue

1. Run:

```powershell
SelfSnap doctor
SelfSnap diag
```

2. Check the Diagnostics tab in Settings for scheduler, activity, storage, retention, notification, and operational summaries.
3. If the problem persists, use the tray `Report Issue` action.
4. Include a short reproduction summary and relevant diagnostics output.

## 6. Update Or Reinstall

### Reinstall from the current checkout

```powershell
SelfSnap reinstall
```

### Check for updates only

```powershell
SelfSnap update --check-only
```

### Update when a newer release is available

```powershell
SelfSnap update
```

The tray menu also exposes update and reinstall actions under the App section.

## 7. Uninstall

Interactive uninstall:

```powershell
SelfSnap uninstall
```

Remove user data too:

```powershell
SelfSnap uninstall --remove-user-data
```

Use `--yes` only when you intentionally want to skip the confirmation prompt.

## Related Docs

- `INSTALL_AND_UPDATE.md`
- `CLI_REFERENCE.md`
- `TROUBLESHOOTING.md`
- `CONFIG_REFERENCE.md`