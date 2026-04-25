# Reference: Core Extraction Map

[ARCHIVED STARTER KIT]
This file is part of the archived starter-kit pack preserved in [README.md](README.md).
It is reference material for reuse and extraction work, not the active SelfSnap product or maintainer contract.

This file is the working extraction map for turning SelfSnap into a reusable Windows tray app starter.

## Context map

### Keep as starter core

| File | Why keep it | Starter action |
|---|---|---|
| `src/selfsnap/paths.py` | Clean Windows path conventions and app data boundaries | Rename app constants and keep structure |
| `src/selfsnap/config_store.py` | Safe JSON config load and atomic save | Reuse as-is, then change model fields |
| `src/selfsnap/logging_setup.py` | Rotating local logging with sane defaults | Reuse as-is |
| `src/selfsnap/runtime_launch.py` | Good background launch contract for `python.exe` and `pythonw.exe` | Reuse and rename command targets |
| `src/selfsnap/runtime_probe.py` | Good preflight diagnostics pattern | Reuse and change dependency checks |
| `src/selfsnap/scheduler/backends.py` | Strong scheduler abstraction seam | Reuse as-is |
| `src/selfsnap/scheduler/task_scheduler.py` | Windows Task Scheduler integration already works | Reuse with new task prefix and worker invocation |
| `src/selfsnap/tray/startup.py` | Startup shortcut creation and removal | Reuse with new shortcut name |
| `src/selfsnap/recurrence.py` | Useful interval math for recurring jobs | Reuse if the new app needs recurring work |
| `src/selfsnap/tray/schedule_editor.py` | Ready-made schedule form behavior | Reuse only if scheduling belongs in the starter |

### Split before reuse

| File | Current problem | Starter action |
|---|---|---|
| `src/selfsnap/models.py` | Generic config is mixed with screenshot settings | Split into base app config and app-specific config |
| `src/selfsnap/tray/app.py` | Tray shell, scheduler, window opening, notifications, and app logic are all mixed | Extract tray shell, action registry, and hook points |
| `src/selfsnap/cli.py` | Command set is SelfSnap-specific | Keep parser pattern, replace handlers |
| `src/selfsnap/db.py` | Solid SQLite helpers, but schema expectations are domain-specific | Reuse connection pattern, rebuild schema |
| `src/selfsnap/lifecycle_actions.py` | Good script invocation layer, but app naming is baked in | Keep structure, parameterize script names |

### Replace for every new app

| File | Why replace it |
|---|---|
| `src/selfsnap/worker.py` | Screenshot domain worker |
| `src/selfsnap/capture_engine.py` | Screenshot capture backend |
| `src/selfsnap/records.py` | Screenshot record schema |
| `src/selfsnap/issue_reporting.py` | SelfSnap-specific issue payloads |
| `src/selfsnap/tray/first_run.py` | SelfSnap first-run content |
| `src/selfsnap/tray/settings_window.py` | SelfSnap settings surface |
| `src/selfsnap/tray/recent_captures_window.py` | SelfSnap content |
| `src/selfsnap/tray/statistics_window.py` | SelfSnap content |
| `src/selfsnap/tray/report_issue_window.py` | SelfSnap content |
| `src/selfsnap/ui_labels.py` | SelfSnap words, warnings, and labels |

## Tests worth carrying forward

| Test file | Contract worth preserving |
|---|---|
| `tests/unit/test_config_store.py` | config creation, atomic save, round-trip load |
| `tests/unit/test_models.py` | validation-first dataclass contract |
| `tests/unit/test_runtime_launch.py` | launch metadata and interpreter resolution |
| `tests/unit/test_schedule_editor.py` | schedule editor and form semantics |

## Existing constraints worth preserving

- Windows 11-only posture
- local-first runtime
- no hidden network traffic by default
- background jobs launched out of process
- thin entry-point files and testable importable logic
- strict config validation before persistence

## Recommended starter tree

```text
src/appname/
  __init__.py
  __main__.py
  cli.py
  models.py
  paths.py
  config_store.py
  logging_setup.py
  runtime_launch.py
  runtime_probe.py
  lifecycle_actions.py
  version.py
  main_window.py
  tray_main.py
  worker.py
  scheduler/
    __init__.py
    backends.py
    task_scheduler.py
  tray/
    __init__.py
    app.py
    startup.py
```

## Target tray menu for the starter

- `Open`
- `Run Now`
- `Enable` or `Disable`
- `Settings` optional
- `Restart`
- `Exit`

Everything else belongs in the primary window unless the app proves it needs a separate dialog.

## Key starter seams

The starter should expose these seams explicitly:

| Seam | Purpose |
|---|---|
| `AppContext` | resolved paths, config, logger, and service registry |
| `ActionRegistry` | tray and window actions without hardwired imports |
| `WindowFactory` | opens the primary window and optional child dialogs |
| `JobRunner` | background work contract |
| `NotificationPolicy` | decides when to show tray notices or overlays |
| `ManifestLoader` | turns the intake form or JSON manifest into runtime UI choices |

## Risk list

- Reusing `models.py` without splitting it will leak screenshot settings into every derived app.
- Reusing `tray/app.py` without refactoring it will make every app harder to change.
- Keeping too many windows in the starter will reduce the speed advantage of standardization.
- Building automation before freezing the starter contracts will automate the wrong shape.