# Install And Update

SelfSnap is currently a source-based Windows 11 application. The supported path is to work from a repository checkout with a local `.venv`.

## Core Rule

Always use the checkout-local virtual environment created by `scripts/setup.ps1`.

- If the local `.venv` exists, SelfSnap redirects into it when you start the app from the wrong interpreter.
- If the local `.venv` does not exist, SelfSnap tells you to run `scripts/setup.ps1`.

## Prerequisites

You need:

- Windows 11
- a normal desktop session for capture work
- Python 3.11 or 3.12, or `uv` so the setup script can resolve one for you

## First-Time Setup

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

What `setup.ps1` does:

1. resolves a suitable Python interpreter,
2. creates or recreates `.venv`,
3. installs the package into that environment,
4. installs dev extras unless `-NoDev` is used,
5. runs `selfsnap doctor` as a final runtime check.

The script prints the `.venv` path and the interpreter it selected.

## First Install For Daily Use

After setup, install the wrapper and startup integration:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

What `install.ps1` does:

1. prefers `.venv\Scripts\python.exe`,
2. installs SelfSnap from the current checkout,
3. creates `%LOCALAPPDATA%\SelfSnap\bin\SelfSnap.cmd`,
4. adds that bin directory to your user `PATH` if needed,
5. writes install metadata used by lifecycle actions,
6. runs `SelfSnap.cmd sync-scheduler`,
7. creates or removes the startup shortcut depending on your config.

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

Use reinstall when the wrapper already exists and you want to refresh the installed state from your current branch.

```powershell
SelfSnap reinstall
```

Optional tray relaunch:

```powershell
SelfSnap reinstall --relaunch-tray
```

Equivalent script form from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reinstall.ps1
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
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Then retry the command from the same checkout.

## Wrapper not found on `PATH`

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

or use the full wrapper path:

```powershell
$env:LOCALAPPDATA\SelfSnap\bin\SelfSnap.cmd tray
```

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