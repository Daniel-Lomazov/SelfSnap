# SelfSnap Starter Kit

[ARCHIVED REFERENCE]
This folder is starter-kit and reuse guidance.
It is not part of the active SelfSnap product or maintainer contract for the current HEAD.
Use [docs/README.md](../../README.md) first when you need current guidance.

## Navigation

- [../../../README.md](../../../README.md): top-level product overview and quick-start hub
- [../../README.md](../../README.md): full docs map
- [../README.md](../README.md): archive hub
- [../../developer/README.md](../../developer/README.md): current maintainer-doc hub

This folder turns SelfSnap from a single product into a reusable Windows tray-app factory.

## What This Kit Is For Now

Use this folder when you need to:
- study how SelfSnap could be extracted into a reusable tray-app starter,
- trace which current app behaviors were considered worth keeping during extraction planning,
- reuse the planning templates and architectural guidance for a future Windows tray utility.

Do not treat this folder as required reading for current SelfSnap usage, maintenance, or release work.

The goal is not to preserve every SelfSnap feature. The goal is to preserve the strong parts:

- Windows tray bootstrapping
- dependable local config and logging
- background worker launch patterns
- Task Scheduler integration for coarse jobs
- tkinter window patterns that are easy to replace

The recommended starter target is narrower than the current app:

- one tray icon
- one primary window
- optional extra dialogs later
- pluggable buttons, toggles, links, status blocks, and background jobs

## Suggested Reading Order

1. [05_Project_Intake_Form.md](05_Project_Intake_Form.md)
2. [04_Target_Architecture.md](04_Target_Architecture.md)
3. [02_How_To_Spin_Up.md](02_How_To_Spin_Up.md)
4. [03_Extraction_Map.md](03_Extraction_Map.md)
5. [01_Tutorial.md](01_Tutorial.md)
6. [06_Starter_Extraction_Plan.md](06_Starter_Extraction_Plan.md)

## What This Kit Gives You

- a code-backed extraction map for what to keep, split, and replace
- a standard form for turning an idea into an app manifest
- an example archived tray-app manifest in [tray_app_factory_manifest.example.json](tray_app_factory_manifest.example.json)
- a repeatable one-night build flow for producing many similar tray apps
- a target architecture that stays Windows-native, local-first, and easy to extend
- a phased extraction plan for converting the current repo into a reusable starter

## What This Kit Does Not Do Yet

- generate the new app automatically
- refactor SelfSnap into a reusable framework package
- replace tkinter or pystray with another UI stack

That is intentional. The fastest route to ten or twenty apps is to standardize the decisions first, then automate the copy and rename phase later.