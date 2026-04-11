# Starter Extraction Plan

This is the practical sequence for turning the current SelfSnap codebase into a reusable tray-app starter.

The plan is intentionally phased. Do not try to generalize everything at once.

## Phase 1: Freeze the starter contract

Goal: decide what every derived app will inherit.

Deliverables:

- one primary window model
- one standard tray menu shape
- one intake form
- one manifest shape
- one baseline CLI command set

Decisions to lock now:

- Windows-only remains in scope
- `pystray` and `tkinter` remain the default UI stack
- local JSON config remains the default persistence layer
- SQLite is optional, not mandatory, in the starter

## Phase 2: Split generic from app-specific config

Goal: remove screenshot-only settings from the starter core.

Implementation tasks:

1. Create a base config model for app-level concerns:
   - app enabled state
   - startup behavior
   - tray visibility options
   - window size
   - scheduler sync state
   - generic storage settings only if the starter needs them
2. Move screenshot-specific fields into a SelfSnap-only extension model.
3. Keep the current validation-first dataclass pattern.

Done when:

- a derived app can reuse config persistence without inheriting image settings

## Phase 3: Refactor the tray shell

Goal: turn `tray/app.py` into infrastructure instead of product logic.

Implementation tasks:

1. Introduce an `AppContext` object.
2. Introduce an `ActionRegistry` for tray and window actions.
3. Move menu actions out of direct imports and into named callbacks.
4. Move SelfSnap-only housekeeping and worker behavior into app services.
5. Keep the event loop, notification plumbing, and icon refresh logic in the shell.

Done when:

- the tray shell can run with a different app window and a different worker without changing shell internals

## Phase 4: Replace many windows with one primary window

Goal: make the starter fast to customize.

Implementation tasks:

1. Create `main_window.py` as the standard primary surface.
2. Define reusable sections:
   - hero
   - status cards
   - actions
   - toggles
   - links
   - diagnostics
3. Rebuild SelfSnap's own UI by composing those sections instead of spreading basic controls across many dialogs.
4. Keep extra dialogs optional.

Done when:

- a new app can be launched with one window file and a manifest-driven section list

## Phase 5: Normalize the worker contract

Goal: let each derived app change behavior without rewriting launch infrastructure.

Implementation tasks:

1. Define a generic job result model:
   - job id
   - success flag
   - status category
   - user message
   - optional payload path or record id
2. Keep `runtime_launch.py` and replace only the worker implementation.
3. Make the tray shell react to generic job results, not screenshot records.

Done when:

- the tray can launch any background job and display consistent status feedback

## Phase 6: Make scheduling optional

Goal: keep the starter light for apps that do not need recurrence.

Implementation tasks:

1. Wrap scheduler behavior behind a feature flag or optional service.
2. Keep recurrence and Task Scheduler modules available.
3. Do not force schedule UI into every derived app.

Done when:

- manual-only apps do not carry schedule complexity in the UI

## Phase 7: Create the starter repository

Goal: publish the reusable shell as its own codebase or branch.

Recommended contents:

- generic tray shell
- primary window framework
- manifest loader
- standard scripts
- starter tests
- starter docs
- one sample app

Done when:

- a new repository can be created from the starter without deleting large chunks of SelfSnap-specific code first

## Phase 8: Automate the factory

Goal: go from idea to working starter app with minimal hand editing.

Implementation tasks:

1. Freeze the JSON manifest schema.
2. Add a scaffold command or script.
3. Generate:
   - package rename
   - app name constants
   - tray title
   - primary window sections
   - button and toggle definitions
   - sample worker stubs
4. Keep the generated output intentionally simple.

Done when:

- a filled manifest can produce a working tray app shell in one pass

## Suggested order of real implementation

1. Split models
2. Refactor tray shell
3. Introduce one primary window
4. Normalize worker contract
5. Make scheduler optional
6. Extract starter repo
7. Automate scaffold generation

If you reverse that order, you will automate too much unstable structure.