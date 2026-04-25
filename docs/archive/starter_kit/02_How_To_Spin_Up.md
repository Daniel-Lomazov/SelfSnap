# How To: Spin Up A Standard Tray App In One Night

[ARCHIVED STARTER KIT]
This file is part of the archived starter-kit pack preserved in [README.md](README.md).
It is reference material for reuse and extraction work, not the active SelfSnap product or maintainer contract.

This guide is the repeatable factory flow.

Use it when you already know the idea and want a working standardized tray app fast.

## Inputs

You need only three things:

1. A filled `05_Project_Intake_Form.md`
2. A new repo or working copy
3. A decision that the first release will use one primary window

## Build sequence

### 1. Name the app once

Choose and lock:

- product name
- Python package name
- tray title
- `%LOCALAPPDATA%` folder name
- Task Scheduler prefix

Do this first so you do not rename the same concepts all night.

### 2. Copy the reusable core

Start from the modules listed in `03_Extraction_Map.md` under `Keep as starter core`.

Do not copy every SelfSnap file blindly. The screenshot-specific files will only slow you down.

### 3. Replace the window layer

Create one primary window with these optional sections:

- summary text
- action buttons
- toggle rows
- status cards
- link list
- footer diagnostics

If a control does not exist in the intake form, do not add it.

### 4. Replace the domain worker

Keep the subprocess launch pattern, but swap out the screenshot worker for the new app's job runner.

Your worker API should answer four questions:

- what job was requested
- what inputs were resolved
- whether it succeeded
- what message should be shown to the user

### 5. Reduce the CLI

The starter CLI only needs a small baseline:

- `tray`
- `run-job` or an equivalent app-specific command
- `doctor`
- `diag` if you want richer diagnostics

Add more commands only when the app actually needs them.

### 6. Keep local persistence boring

Reuse the existing config and logging patterns. Prefer local JSON plus SQLite only if the app truly needs queryable history.

Use this rule:

- JSON for settings and manifest-like state
- SQLite only for history, queues, or audit data

### 7. Decide job cadence

Use SelfSnap's scheduling model only when the new app genuinely needs recurring background work.

Use these defaults:

- no scheduler if the app is manual only
- tray polling for seconds or minutes jobs
- Task Scheduler for hourly or daily jobs

### 8. Add only first-release visuals

Support these first:

- one accent color
- one success state
- one warning state
- one error state
- one overlay or toast pattern

Avoid building a complex animation or theme engine on version one.

### 9. Validate the starter before feature work

Before adding real content, confirm:

- tray starts without errors
- startup shortcut can be created and removed
- config saves and reloads
- one button action works
- one toggle persists
- one background job can run without freezing the window

### 10. Freeze the pattern

Once the first new app works, write down only the parts that must stay standard:

- folder layout
- base commands
- config keys
- tray menu shape
- main window section order
- logging and diagnostics contract

Those are the pieces that let you build ten or twenty apps consistently.

## Recommended first-night scope

Keep the first pass inside this box:

- one tray icon
- one main window
- three to six actions
- two to five toggles
- zero or one background scheduler
- zero or one extra dialog

If the idea needs more, split it into release one and release two.