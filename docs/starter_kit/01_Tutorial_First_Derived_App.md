# Tutorial: Build Your First Derived Tray App

This tutorial walks through creating a new app from SelfSnap's tray-shell core in one focused session.

Target outcome:

- one tray icon
- one main window
- a few buttons
- a few toggles
- links
- room for custom visuals and background jobs

For the tutorial, imagine the new app is called `SignalBoard`.

## Before you start

Fill out `05_Project_Intake_Form.md` first. Keep the first derived app intentionally small:

- one primary user persona
- one primary window
- no more than five tray actions
- no more than three background jobs

## Step 1: Copy the repository

Create a new repository from this codebase and rename the Python package from `selfsnap` to your new package name.

For the first pass, keep the folder structure. Do not redesign the tree yet.

## Step 2: Keep the foundation intact

Carry these modules forward with minimal change:

- `paths.py`
- `config_store.py`
- `logging_setup.py`
- `runtime_launch.py`
- `runtime_probe.py`
- `scheduler/backends.py`
- `scheduler/task_scheduler.py`
- `tray/startup.py`

These are the parts that already solve real Windows tray-app problems.

## Step 3: Collapse the UI to one main window

Replace SelfSnap's many windows with a single `main_window.py`.

Your first main window should have five visible zones:

1. App title and short summary
2. Status line or badge row
3. Primary actions
4. Toggles and settings
5. Helpful links

If you need more later, add dialogs after the first version works.

## Step 4: Simplify the tray menu

Keep only the menu items that support the new app's first release:

- `Open`
- `Run Now`
- `Enable` or `Disable`
- `Settings` if needed
- `Restart`
- `Exit`

Move everything else behind the main window.

## Step 5: Replace the worker logic

SelfSnap's worker is screenshot-specific. Your new worker should run the smallest useful job for the new app.

Examples:

- refresh local data
- transform a text file
- render a local report
- sync a folder index
- trigger a small automation

Keep the launch pattern. Replace the business logic.

## Step 6: Wire the intake form into config

Translate the filled intake form into:

- app name and tray title
- window title and default size
- button labels and button actions
- toggle labels and default states
- link labels and destinations
- optional background job list

Store these in config or a starter manifest before you hardcode them into the window.

## Step 7: Keep diagnostics and logging

Even a tiny tray app needs:

- a rotating log file
- a `doctor` command or equivalent
- one place to print resolved paths
- one place to print active job state

This is what lets you build many apps without drowning in support work.

## Step 8: Run the first derived app

The first success bar is low:

- the tray starts cleanly
- the main window opens cleanly
- the toggles persist
- at least one button action works
- at least one background job can be launched

Do not optimize visuals until this works.

## Step 9: Add visual polish last

Once the shell works, add the first layer of presentation:

- a consistent accent color
- one headline font choice
- one status badge style
- one success toast or overlay pattern
- one link style

Small, consistent styling beats a half-built design system.

## You are done when

- the app boots from tray
- the app owns one clear main window
- a filled intake form can explain every visible control
- another person could clone the same flow for a second app without guessing

That is the threshold for a reusable starter.