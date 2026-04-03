# SelfSnap Starter Kit

This folder turns SelfSnap from a single product into a reusable Windows tray-app factory.

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

Use these files in this order:

1. `05_Project_Intake_Form.md`
2. `04_Explanation_Target_Architecture.md`
3. `02_How_To_Spin_Up_A_Standard_Tray_App.md`
4. `03_Reference_Core_Extraction_Map.md`
5. `01_Tutorial_First_Derived_App.md`
6. `06_Starter_Extraction_Plan.md`

What this kit gives you:

- a code-backed extraction map for what to keep, split, and replace
- a standard form for turning an idea into an app manifest
- a repeatable one-night build flow for producing many similar tray apps
- a target architecture that stays Windows-native, local-first, and easy to extend
- a phased extraction plan for converting the current repo into a reusable starter

What this kit does not do yet:

- generate the new app automatically
- refactor SelfSnap into a reusable framework package
- replace tkinter or pystray with another UI stack

That is intentional. The fastest route to ten or twenty apps is to standardize the decisions first, then automate the copy and rename phase later.