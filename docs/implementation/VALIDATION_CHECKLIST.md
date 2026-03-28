# SelfSnap Win11 Validation Checklist

## First run

- Install dependencies or run the source-based install script.
- Run `selfsnap diag` and confirm config, DB, log, Pictures capture, and Pictures archive paths are created.
- Start `selfsnap tray` and confirm a tray icon appears.
- Confirm the first-run dialog states that captures stay local, the runtime is offline by default, and v1 does not encrypt captures at rest.
- Open Settings, then use the tray default action or menu `Report Issue` and confirm the report dialog still opens without affecting Settings geometry.
- Complete the first-run setup dialog and confirm scheduled capture stays OFF unless explicitly enabled there.
- If the tray settings window has been opened and reused, confirm a manual capture does not change its size or reopen it smaller.

## Post-v1 release checks

- Confirm no console window appears during tray startup, scheduled capture, or reconcile activity.
- Confirm storage preset selection updates both capture and archive roots together.
- Confirm the preset mapping is correct:
  - `Local Pictures` -> `%USERPROFILE%\Pictures\SelfSnap\...`
  - `OneDrive Pictures` -> `%OneDrive%\Pictures\SelfSnap\...`
  - manual path edit -> `Custom Folder`
- Confirm `Reset Capture History` requires a destructive warning before it clears SelfSnap user data.
- Confirm reset removes capture files, archive files, DB history, logs, config, startup shortcut, and scheduled tasks, then relaunches first run.
- Confirm the settings window can be resized in both directions and content widens without cropping.
- Confirm a manual capture does not resize an open settings window and that reopening returns to the stable minimum size.
- Confirm reinstall keeps user data and settings by default.
- Confirm the Settings window repeats the local-only / not-encrypted-at-rest warning.
- Confirm `Report Issue` never attaches screenshots, logs, or local file paths automatically.
- Confirm `Report Issue` opens only a browser page and does not submit anything silently from the app.
- If one tray launch shows both a parent `.venv` `pythonw.exe` and a child `uv`-backed `pythonw.exe` in Task Manager, do not treat that alone as a failure. Only treat it as a bug if duplicate tray icons, duplicate notifications, or duplicate Settings windows appear.

## Manual capture

- Use tray `Capture Now` or run `selfsnap capture --trigger manual`.
- Confirm image file(s) are written under the configured capture root using the selected image format.
- If capture mode is `per_monitor`, confirm one file per display is written.
- Confirm the SQLite database contains a `capture_saved` record.
- Confirm the log file records the run without leaking content details.

## Scheduled capture

- Add at least one schedule in Settings.
- Save Settings and confirm scheduler sync succeeds immediately, or that a persistent failed-sync warning appears.
- Confirm `schtasks /Query` shows `SelfSnap.Capture.<schedule_id>`.
- Wait for the schedule or temporarily set a near-future time.
- Confirm the scheduled capture creates image file(s) in the selected format and a metadata row.

## Failure and status handling

- Disable scheduled captures and wait past a schedule time.
- Confirm no scheduled run occurs while disabled.
- Temporarily make the capture root invalid and confirm failures are recorded honestly.
- Force a scheduler sync failure and confirm manual capture still works while scheduled capture is blocked.

## Output verification

- Confirm filenames use the `cap_YYYY-MM-DD_HH-MM-SS_...` prefix and the configured file extension.
- Confirm the latest record can be opened from the tray.
- Confirm the capture folder opens from the tray.
- Confirm `Report Issue` opens a GitHub issue page in the browser.
- If notifications are enabled, confirm failed or missed events notify and successful captures only notify when that toggle is ON.

## Retention

- Set retention to `keep_days = 1`.
- Insert or create an old test capture.
- Run manual capture or wait for tray housekeeping.
- Confirm the old PNG is moved into the archive and the DB row is marked `archived = 1` with `archived_at_utc`.

## Packaging and install

- Run `scripts/install.ps1`.
- Use tray `Reinstall` and confirm the app reinstalls, closes, relaunches, and preserves user data.
- Use tray `Check for Updates` on both an up-to-date checkout and a newer tagged release, and confirm it only mutates the local checkout when a newer release exists.
- If `pythonw.exe` is nonstandard, confirm `scripts/install.ps1 -PythonwExe ...` resolves it correctly.
- Confirm `%LOCALAPPDATA%\SelfSnap\bin\SelfSnap.cmd` exists.
- Confirm the Startup-folder shortcut points to a windowless tray launch, not the CLI wrapper.
- Log off and back on.
- Confirm the tray starts at logon and scheduled tasks still function.
- Run `scripts/uninstall.ps1` and confirm captures, archive, config, DB, and logs are preserved.
- Use tray `Uninstall -> Remove All User Data` only on disposable test data and confirm the repo checkout and `.venv` remain untouched.
- If the editable package lives in a non-default interpreter, confirm `scripts/uninstall.ps1 -PythonExe ...` still removes it cleanly.
- If stale pytest folders exist, run `scripts/cleanup_pytest_artifacts.ps1 -ListOnly` first, then `scripts/cleanup_pytest_artifacts.ps1`, then `scripts/cleanup_pytest_artifacts.ps1 -RepairAcl` if ownership repair is needed, and confirm they are removed.

## Execution evidence - 2026-03-29 (Phase C, terminal-driven)

Environment snapshot:
- Date: 2026-03-29
- Host: Windows 11 (user workstation)
- Python: 3.12.11 (`.venv\Scripts\python.exe`)
- App version from `selfsnap diag`: `0.9.4`

Completed checks (evidence captured):
- `selfsnap doctor` returned `ok: true` with successful imports for `pystray`, `PIL`, and `mss`.
- `selfsnap diag` confirmed resolved paths, scheduler sync state `ok`, and a latest `capture_saved` record with `file_present: true`.
- Manual capture command completed successfully:
  - `selfsnap capture --trigger manual`
  - File created: `C:\Users\lomaz\Pictures\SelfSnap\captures\2026\03\29\cap_2026-03-29_01-14-43_manual_manual.png`
- Coarse schedule registration validated with Task Scheduler:
  - Injected temporary `hour` schedule: `phasec_hour01`
  - Ran `selfsnap sync-scheduler`
  - Confirmed `schtasks /Query /TN SelfSnap.Capture.phasec_hour01 /FO LIST /V` returned task details including:
    - `TaskName: \SelfSnap.Capture.phasec_hour01`
    - `Status: Ready`
    - `Task To Run: ...pythonw.exe -m selfsnap capture --trigger scheduled --schedule-id phasec_hour01 ...`
  - Restored original config and re-synced to clean up temporary coarse schedule state.
- Full automated functional gate also passed during Phase C prep:
  - `pytest -q` -> `134 passed`
  - Coverage gate met (`80.46%`)

Observed notes:
- `schtasks /Query` did not show `SelfSnap.Capture.*` tasks for the normal minute schedule (`sched_65361833e7aa`), which is expected because minute-level schedules are tray-managed high-frequency behavior.

Pending manual checks (requires interactive tray/UI and/or disposable environment):
- Confirm tray icon visibility, first-run dialog wording, and Settings warning text in UI.
- Confirm `Report Issue` flow from tray and Settings geometry non-regression.
- Confirm scheduled capture registration for at least one coarse schedule (`hours` or above) and verify `schtasks /Query` contains `SelfSnap.Capture.<schedule_id>`.
- Execute failure-path checks for invalid capture root and forced scheduler sync failure while confirming manual capture remains available.
- Run lifecycle flow checks on disposable test data: tray `Reinstall`, `Check for Updates` against newer tag, tray `Uninstall -> Remove All User Data` behavior.
- Run logoff/logon startup check and confirm tray relaunch plus scheduled functionality after sign-in.
