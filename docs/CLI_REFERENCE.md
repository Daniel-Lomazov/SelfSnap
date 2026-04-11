# CLI Reference

This document describes the current command-line surface exposed by `selfsnap`.

After `scripts/install.ps1`, the most convenient entry point is usually `SelfSnap` from your user `PATH`.
Inside the repository checkout, you can also run commands through the local environment with `python -m selfsnap ...`.

## Global Version Flag

```powershell
selfsnap --version
```

Prints the runtime version string and exits.

## Command Summary

| Command | Purpose |
|---|---|
| `selfsnap tray` | Run the tray application |
| `selfsnap capture --trigger ...` | Run a manual or scheduled capture |
| `selfsnap reconcile` | Record missed recurring schedule occurrences |
| `selfsnap sync-scheduler` | Sync Windows Task Scheduler tasks from config |
| `selfsnap reinstall` | Reinstall from the current source checkout |
| `selfsnap uninstall` | Uninstall SelfSnap |
| `selfsnap update` | Check for a release update and optionally install it |
| `selfsnap diag` | Print runtime diagnostics |
| `selfsnap doctor` | Validate runtime dependencies |

## `tray`

```powershell
selfsnap tray
```

Starts the tray application. In a source checkout, SelfSnap expects to run through the local `.venv`.

## `capture`

```powershell
selfsnap capture --trigger manual
selfsnap capture --trigger scheduled --schedule-id morning
selfsnap capture --trigger scheduled --schedule-id morning --planned-local-ts 2026-04-12T09:00:00
```

Arguments:

- `--trigger` required, one of `manual` or `scheduled`
- `--schedule-id` optional for manual capture, expected for scheduled capture flows
- `--planned-local-ts` optional local planned timestamp used by scheduled capture flows

## `reconcile`

```powershell
selfsnap reconcile
```

Runs missed-slot reconciliation for recurring schedules and records any occurrences that should have happened while the app was unavailable.

## `sync-scheduler`

```powershell
selfsnap sync-scheduler
```

Refreshes Windows Task Scheduler tasks from the current config.

Use this when:

- schedules were edited,
- startup or scheduler state looks stale,
- you are validating install or recovery behavior.

## `reinstall`

```powershell
selfsnap reinstall
selfsnap reinstall --relaunch-tray
```

Reinstalls SelfSnap from the current source checkout.

Option:

- `--relaunch-tray` relaunches the tray after reinstall completes

## `uninstall`

```powershell
selfsnap uninstall
selfsnap uninstall --yes
selfsnap uninstall --remove-user-data
selfsnap uninstall --remove-user-data --yes
```

Options:

- `--remove-user-data` also removes config, database, captures, and logs
- `--yes` skips the confirmation prompt

Without `--yes`, SelfSnap prompts before uninstalling.

## `update`

```powershell
selfsnap update --check-only
selfsnap update
selfsnap update --relaunch-tray
```

Options:

- `--check-only` only reports whether an update is available
- `--relaunch-tray` relaunches the tray after the update completes

`update` checks GitHub Releases for a newer tag before attempting an install.

## `diag`

```powershell
selfsnap diag
```

Prints a JSON diagnostics payload that includes:

- version,
- resolved application paths,
- current config,
- resolved storage roots,
- latest record summary,
- scheduled-task details,
- runtime probe results,
- Python version,
- current working directory.

Use this when reporting issues or validating install/runtime state.

## `doctor`

```powershell
selfsnap doctor
```

Prints a JSON runtime dependency probe and exits with `0` when dependencies are healthy or `1` when they are not.

Use this first when setup, Pillow, tray, or runtime dependencies seem broken.

## Source Checkout Notes

In a source checkout:

- SelfSnap expects the local `.venv` created by `scripts/setup.ps1`.
- If you launch the app from the wrong interpreter and `.venv` exists, it redirects into the local environment.
- If `.venv` does not exist, it tells you to run `scripts/setup.ps1`.

## Related Docs

- `INSTALL_AND_UPDATE.md`
- `TROUBLESHOOTING.md`
- `WORKFLOWS.md`