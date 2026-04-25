# Install And Update

SelfSnap is currently a source-based Windows 11 application. The supported path is to work from a repository checkout with a local `.venv`.
This guide tracks the current stable public release line.

## Core Rule

Always use the checkout-local virtual environment created by `scripts/user/setup.ps1`.

- If the local `.venv` exists, SelfSnap redirects into it when you start the app from the wrong interpreter.
- If the local `.venv` does not exist, SelfSnap tells you to run `scripts/user/setup.ps1`.

## Prerequisites

You need:

- Windows 11
- a normal desktop session for capture work
- Python 3.11 or 3.12, or `uv` so the setup script can resolve one for you

## First-Time Setup

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\user\setup.ps1
```

What `scripts/user/setup.ps1` does:

1. resolves a suitable Python interpreter,
2. creates or recreates `.venv`,
3. installs the package into that environment,
4. installs dev extras unless `-NoDev` is used,
5. runs `selfsnap doctor` as a final runtime check.

If `uv venv --clear` cannot remove `.venv\Scripts` because another process is holding files there, the setup script retries in place with `--allow-existing` before it gives up.
It also stops known background tool executables from `.venv\Scripts` such as `ruff.exe` before retrying recreation or installing packages.
If a tool respawns and relocks `.venv\Scripts` during the dev-extras install, setup retries that pass after stopping the locking process again.
If a locked developer tool still prevents a full dev-refresh pass, the script keeps the runtime environment usable, warns you, and tells you to rerun setup after closing the locking tool.

The script prints the `.venv` path and the interpreter it selected.

## First Install For Daily Use

After setup, install the wrapper and startup integration:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\user\install.ps1
```

What `scripts/user/install.ps1` does:

1. prefers `.venv\Scripts\python.exe`,
2. installs SelfSnap from the current checkout,
3. creates `%LOCALAPPDATA%\SelfSnap\bin\SelfSnap.cmd`,
4. adds that bin directory to your user `PATH` if needed,
5. writes install metadata used by lifecycle actions,
6. runs `SelfSnap.cmd sync-scheduler`, unless your existing config is from a newer schema than this checkout supports,
7. creates or removes the startup shortcut depending on your config, unless that newer-schema safety check skips config mutation.

If your existing `%LOCALAPPDATA%\SelfSnap\config\config.json` is from a newer schema than the current checkout supports, install still writes the wrapper and metadata but skips scheduler sync and startup shortcut updates so this checkout does not rewrite a config it cannot safely preserve.

## Start The Tray

After install:

```powershell
SelfSnap tray
```

From a checkout without using the wrapper:

```powershell
.venv\Scripts\Activate.ps1
python -m selfsnap tray
```

## Reinstall From The Current Checkout

Use reinstall when the wrapper already exists and you want to refresh the installed state from your current checkout.

```powershell
SelfSnap reinstall
```

Optional tray relaunch:

```powershell
SelfSnap reinstall --relaunch-tray
```

Equivalent script form from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\user\reinstall.ps1
```

## Check For Updates

To check GitHub for a newer tagged release without installing it:

```powershell
SelfSnap update --check-only
```

To install an available update:

```powershell
SelfSnap update
```

Optional tray relaunch after update:

```powershell
SelfSnap update --relaunch-tray
```

The tray menu exposes the same update and reinstall flows under App actions.

## Uninstall

Interactive uninstall:

```powershell
SelfSnap uninstall
```

Remove user data as well:

```powershell
SelfSnap uninstall --remove-user-data
```

Non-interactive uninstall:

```powershell
SelfSnap uninstall --yes
SelfSnap uninstall --remove-user-data --yes
```

## Quick Recovery Paths

## `.venv` missing or wrong interpreter used

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\user\setup.ps1
```

Then retry the command from the same checkout.

## Setup fails with access denied under `.venv\Scripts`

The most common cause is another process still holding files inside `.venv\Scripts`.
Examples include an activated shell, editor tooling, or another Python process from the same checkout.

Run `scripts/user/setup.ps1` again first. It now retries in place with `uv venv --allow-existing` when the clear step cannot remove `.venv\Scripts`.
It also stops known background tool executables from `.venv\Scripts` such as `ruff.exe` before package installation.

If it still fails:

1. close shells, editors, or Python processes that may be using `.venv`,
2. rerun `powershell -ExecutionPolicy Bypass -File .\scripts\user\setup.ps1`, or
3. pass `-VenvPath` to create a different environment path temporarily.

## Wrapper not found on `PATH`

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\user\install.ps1
```

or use the full wrapper path:

```powershell
$env:LOCALAPPDATA\SelfSnap\bin\SelfSnap.cmd tray
```

## Install reports a newer `schema_version`

This checkout can lag behind a config written by a newer checkout.

If `scripts/user/install.ps1` warns that your config schema is newer than the current checkout supports, the source install itself still completed. What was skipped is the config-mutating integration work: scheduler sync and startup shortcut updates.

Current builds in this repository support the schema-4 extraction-related config fields, so this warning now indicates a genuinely newer checkout/config mismatch.

Use one of these recovery paths:

1. switch back to a checkout that supports that newer config schema,
2. back up `%LOCALAPPDATA%\SelfSnap\config\config.json` and reset it if you intentionally want to run the older checkout, or
3. keep the current config file and avoid running this older checkout against it.

## Startup behavior not matching Settings

Run:

```powershell
SelfSnap sync-scheduler
SelfSnap diag
```

Then verify `start_tray_on_login` and scheduler state in Settings.

## Related Docs

- `CLI_REFERENCE.md`
- `TROUBLESHOOTING.md`
- `CONFIG_REFERENCE.md`
- `WORKFLOWS.md`