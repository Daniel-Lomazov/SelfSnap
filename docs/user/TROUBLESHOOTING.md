# Troubleshooting

When SelfSnap behaves unexpectedly, start with the built-in diagnostics before changing settings blindly.
This guide tracks the current preview build, not a stable release.

## Start Here

```powershell
SelfSnap doctor
SelfSnap diag
```

Use `doctor` to validate runtime dependencies.
Use `diag` to inspect the current version, paths, config, scheduler state, and latest capture result.

## Setup And Launch Problems

## SelfSnap says the local `.venv` is missing

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\user\setup.ps1
```

Then retry the command from the same checkout.

## Setup fails with access denied under `.venv\Scripts`

This usually means another process still has a file handle open inside `.venv\Scripts`.

Try this order:

1. rerun `powershell -ExecutionPolicy Bypass -File .\scripts\user\setup.ps1` once, because the script now retries in place with `uv venv --allow-existing` after a failed clear,
2. let the script stop known background tool processes from `.venv\Scripts` such as `ruff.exe`,
3. if it still fails, close shells, editors, or Python processes using `.venv`,
4. rerun the setup script from the repository root,
5. if you need to keep the locked environment alive temporarily, rerun with `-VenvPath` to create a different environment path.

If setup completes with a warning that development extras could not be fully refreshed, the runtime environment is still usable. Close the locking tool, then rerun `scripts/user/setup.ps1` if you need the full dev toolchain.

## The wrapper command is not recognized

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\user\install.ps1
```

This recreates `%LOCALAPPDATA%\SelfSnap\bin\SelfSnap.cmd` and adds the bin folder to your user `PATH` if needed.

## Install warns that config `schema_version` is newer than this checkout

This repository tracks a preview build, not a stable release. That means your existing `%LOCALAPPDATA%\SelfSnap\config\config.json` can be newer than the current checkout.

When that happens, `scripts/user/install.ps1` still completes the wrapper install but skips scheduler sync and startup shortcut updates so it does not rewrite a newer config with an older preview build.

If you need full install integration again:

1. use a checkout that supports your current config schema,
2. or back up and reset `%LOCALAPPDATA%\SelfSnap\config\config.json` before rerunning install.

## The tray is already running or the icon looks duplicated

Try this order:

1. Exit the app from the tray menu.
2. Start it again once with `SelfSnap tray`.
3. If you still suspect stale tray state, run `SelfSnap reinstall` and relaunch.

SelfSnap is designed to keep only one live tray runtime. Stale Windows notification-area icons can outlive the process briefly even after the real process exits.

## Scheduler Problems

## Scheduler says it needs attention

Run:

```powershell
SelfSnap sync-scheduler
SelfSnap diag
```

Then check the scheduler status in the tray or Settings.

## Scheduled captures are paused unexpectedly

Check both:

- the tray pause/resume state,
- the `Scheduled captures enabled` checkbox in Settings.

If you changed schedules or startup behavior recently, save Settings and run `SelfSnap sync-scheduler` again.

## Captures missing after sleep or wake

This can be expected in some sleep windows. SelfSnap treats wake-based scheduling as best effort, not a guarantee.

Recommended steps:

1. inspect the latest outcome in the tray or Settings,
2. run `SelfSnap diag`,
3. keep the machine awake during critical capture windows,
4. prefer more conservative scheduling if sleep/wake reliability is essential.

## Storage Problems

## OneDrive storage preset stops working

If OneDrive becomes unavailable, capture writes can fail.

Recovery path:

1. open Settings,
2. switch storage preset to `Local Pictures`,
3. save,
4. run a manual capture,
5. run `SelfSnap diag` to confirm the resolved paths.

## Manual Capture Or UI Problems

## Capture Now does nothing obvious

Use `Capture Now`, wait a few seconds, then check:

- latest capture summary in Settings,
- tray status,
- `SelfSnap diag` output,
- configured storage location.

## The Settings window is open while tray state changes

The Settings window polls external config changes. Local unsaved changes in Settings should win until you save or close, but it is still best to save once you finish editing scheduler-related settings.

## Update, Reinstall, And Uninstall Problems

## Update check cannot reach GitHub

`SelfSnap update` requires network access to GitHub Releases.

If the check fails:

1. verify internet access,
2. retry `SelfSnap update --check-only`,
3. use `SelfSnap reinstall` if you only need to refresh the current checkout.

## Reinstall or uninstall fails

Run the command again from a normal PowerShell session and then inspect `SelfSnap diag`.

If needed, retry using the script directly from the repository root.

## Reporting An Issue Safely

Use the tray `Report Issue` action when possible.

It is browser-only and always opens a prefilled GitHub issue page under user control.

Include:

- what you were doing,
- what happened instead,
- relevant `SelfSnap doctor` and `SelfSnap diag` output,
- whether the problem is reproducible.

Automatically included diagnostics should stay limited to safe runtime metadata such as app version, storage preset, scheduler sync state, and latest outcome code.
SelfSnap does not automatically attach screenshots, logs, local file paths, or database contents.

## Related Docs

- `INSTALL_AND_UPDATE.md`
- `CLI_REFERENCE.md`
- `CONFIG_REFERENCE.md`
- `WORKFLOWS.md`