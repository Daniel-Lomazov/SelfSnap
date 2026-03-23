# SelfSnap Win11 Validation Checklist

## First run

- Install dependencies or run the source-based install script.
- Run `selfsnap diag` and confirm config, DB, log, Pictures capture, and Pictures archive paths are created.
- Start `selfsnap tray` and confirm a tray icon appears.
- Complete the first-run setup dialog and confirm scheduled capture stays OFF unless explicitly enabled there.
- If the tray settings window has been opened and reused, confirm a manual capture does not change its size or reopen it smaller.

## Post-v1 release checks

- Confirm no console window appears during tray startup, scheduled capture, or reconcile activity.
- Confirm storage preset selection updates both capture and archive roots together.
- Confirm the preset mapping is correct:
  - `Local Pictures` -> `%USERPROFILE%\Pictures\SelfSnap\...`
  - `OneDrive` -> `%OneDrive%\Pictures\SelfSnap\...`
  - manual path edit -> `custom`
- Confirm `Reset Capture History` requires a destructive warning before it clears SelfSnap user data.
- Confirm reset removes capture files, archive files, DB history, logs, config, startup shortcut, and scheduled tasks, then relaunches first run.
- Confirm the settings window can be resized and content does not crop.
- Confirm a manual capture does not resize an open settings window and that reopening returns to the stable minimum size.
- Confirm reinstall keeps user data and settings by default.

## Manual capture

- Use tray `Capture Now` or run `selfsnap capture --trigger manual`.
- Confirm a PNG is written under the configured capture root.
- Confirm the SQLite database contains a `capture_saved` record.
- Confirm the log file records the run without leaking content details.

## Scheduled capture

- Add at least one schedule in Settings.
- Save Settings and confirm scheduler sync succeeds immediately, or that a persistent failed-sync warning appears.
- Confirm `schtasks /Query` shows `SelfSnap.Capture.<schedule_id>`.
- Wait for the schedule or temporarily set a near-future time.
- Confirm the scheduled capture creates a PNG and metadata row.

## Failure and status handling

- Disable scheduled captures and wait past a schedule time.
- Confirm no scheduled run occurs while disabled.
- Temporarily make the capture root invalid and confirm failures are recorded honestly.
- Force a scheduler sync failure and confirm manual capture still works while scheduled capture is blocked.

## Output verification

- Confirm filenames follow `cap_YYYY-MM-DD_HH-MM-SS_trigger_schedule.png`.
- Confirm the latest record can be opened from the tray.
- Confirm the capture folder opens from the tray.
- If notifications are enabled, confirm failed or missed events notify and successful captures only notify when that toggle is ON.

## Retention

- Set retention to `keep_days = 1`.
- Insert or create an old test capture.
- Run manual capture or wait for tray housekeeping.
- Confirm the old PNG is moved into the archive and the DB row is marked `archived = 1` with `archived_at_utc`.

## Packaging and install

- Run `scripts/install.ps1`.
- If `pythonw.exe` is nonstandard, confirm `scripts/install.ps1 -PythonwExe ...` resolves it correctly.
- Confirm `%LOCALAPPDATA%\SelfSnap\bin\SelfSnap.cmd` exists.
- Confirm the Startup-folder shortcut points to a windowless tray launch, not the CLI wrapper.
- Log off and back on.
- Confirm the tray starts at logon and scheduled tasks still function.
- Run `scripts/uninstall.ps1` and confirm captures, archive, config, DB, and logs are preserved.
- If the editable package lives in a non-default interpreter, confirm `scripts/uninstall.ps1 -PythonExe ...` still removes it cleanly.
- If stale pytest folders exist, run `scripts/cleanup_pytest_artifacts.ps1 -ListOnly` first, then `scripts/cleanup_pytest_artifacts.ps1 -Aggressive` from an elevated shell and confirm they are removed.
