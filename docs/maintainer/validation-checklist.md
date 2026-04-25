# SelfSnap Win11 Validation Checklist

This maintainer checklist is the active reusable validation surface for current release work.
Historical execution evidence and retired release-specific QA notes live under `../archive/releases/`.

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
- Confirm launching from a non-local interpreter redirects or blocks with guidance to create/use `.venv`.
- Confirm storage preset selection updates both capture and archive roots together.
- Confirm the preset mapping is correct:
  - `Local Pictures` -> `%USERPROFILE%\Pictures\SelfSnap\...`
  - `OneDrive Pictures` -> `%OneDrive%\Pictures\SelfSnap\...`
  - manual path edit -> `Custom Folder`
- Confirm `Reset Capture History` requires a destructive warning before it clears SelfSnap user data.
- Confirm reset removes capture files, archive files, DB history, logs, config, startup shortcut, and scheduled tasks, then relaunches first run.
- Confirm the settings window can be resized in both directions and content widens without cropping.
- Confirm card layouts reflow between stacked and split modes around responsive thresholds without overlap.
- Confirm a manual capture does not resize an open settings window and that reopening returns to the stable minimum size.
- Confirm the Schedules tab reflows list/editor panels correctly at narrow widths.
- Confirm schedule list columns auto-fit label/recurrence/start/status text without truncation regressions.
- Confirm reinstall keeps user data and settings by default.
- Confirm the Settings window repeats the local-only / not-encrypted-at-rest warning.
- Confirm `Report Issue` never attaches screenshots, logs, or local file paths automatically.
- Confirm `Report Issue` opens only a browser page and does not submit anything silently from the app.
- Confirm global and per-schedule enable/disable changes remain consistent under external config polling.
- Toggle schedule enable in Settings without saving while external state changes and confirm the unsaved local value remains visible until save or close updates the baseline.
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

## Historical execution evidence

Archived execution evidence from the 2026-03-29 validation run now lives in `../archive/releases/release_history.md`.
Keep this checklist focused on the reusable validation contract and use the archived evidence file for historical traceability.
