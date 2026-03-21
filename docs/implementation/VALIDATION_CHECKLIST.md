# SelfSnap Win11 Validation Checklist

## First run

- Install dependencies or build the executables.
- Run `selfsnap diag` and confirm config, DB, and log paths are created.
- Start `selfsnap tray` and confirm a tray icon appears.

## Manual capture

- Use tray `Capture Now` or run `selfsnap capture --trigger manual`.
- Confirm a PNG is written under the configured capture root.
- Confirm the SQLite database contains a `capture_saved` record.
- Confirm the log file records the run without leaking content details.

## Scheduled capture

- Add at least one schedule in settings.
- Run `selfsnap sync-scheduler`.
- Confirm `schtasks /Query` shows `SelfSnap.Capture.<schedule_id>`.
- Wait for the schedule or temporarily set a near-future time.
- Confirm the scheduled capture creates a PNG and metadata row.

## Failure and status handling

- Disable scheduled captures and wait for a scheduled time.
- Confirm the result is an explicit skipped status, not a silent absence.
- Pause for 60 minutes and confirm scheduled runs are skipped while paused.
- Temporarily make the capture root invalid and confirm failures are recorded honestly.

## Output verification

- Confirm filenames follow `cap_YYYY-MM-DD_HH-MM-SS_trigger_schedule.png`.
- Confirm the latest record can be opened from the tray.
- Confirm the capture folder opens from the tray.

## Retention

- Set retention to `keep_days = 1`.
- Insert or create an old test capture.
- Run manual capture or wait for tray housekeeping.
- Confirm the old PNG is deleted and the DB row is marked with `retention_deleted_at_utc`.

## Packaging

- Run `scripts/build.ps1`.
- Confirm `dist/SelfSnapTray.exe` and `dist/SelfSnapWorker.exe` exist.
- Run `scripts/install.ps1`.
- Log off and back on.
- Confirm the tray starts at logon and tasks still function.
