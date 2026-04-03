# Project Intake Form

Fill this before you copy code.

If a field is blank, the starter should assume the feature does not exist yet.

## 1. Identity

- Product name:
- Short tagline:
- Python package name:
- Tray title:
- `%LOCALAPPDATA%` folder name:
- Repo name:
- Version for first build:

## 2. Primary user and first release

- Primary user:
- Core job this app does:
- What the user should be able to do in the first five minutes:
- What is explicitly out of scope for release one:

## 3. Primary window

- Window title:
- Default size:
- Opening mode: `normal`, `compact`, or `dashboard`
- Top summary text:
- Sections to show, in order:
- Do you need status badges:
- Do you need a footer diagnostics area:

## 4. Buttons

List each button on its own line.

| Button label | Purpose | Action id | Needs background job? | Success message |
|---|---|---|---|---|
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

## 5. Toggles

List each toggle on its own line.

| Toggle label | Config key | Default | Visible in tray? | Notes |
|---|---|---|---|---|
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

## 6. Text blocks and links

| Type | Label or heading | Target or body | Notes |
|---|---|---|---|
| text |  |  |  |
| link |  |  |  |
| text |  |  |  |

## 7. Visual language

- Accent color:
- Surface color:
- Success color:
- Warning color:
- Error color:
- Preferred font family:
- Do you want a success toast or overlay:
- Do you want icons or emoji-free text only:
- Do you want light-only, dark-only, or fixed theme:

## 8. Tray menu

Keep this short.

- Default tray action:
- Menu items in order:
- Which menu items mirror buttons from the main window:
- Does the tray need live status text:

## 9. Background jobs

List each job on its own line.

| Job id | Trigger type | Trigger details | User-visible result | Failure result |
|---|---|---|---|---|
|  | manual |  |  |  |
|  | scheduled |  |  |  |
|  | startup |  |  |  |

## 10. Persistence

- Config needs:
- Need SQLite history: yes or no
- If yes, what records must be stored:
- Local folders needed besides logs and config:
- Need custom storage presets: yes or no

## 11. Extra windows

Only list windows that release one truly needs.

| Window name | Purpose | Opened from | Can this wait until later? |
|---|---|---|---|
|  |  |  |  |

## 12. Install and lifecycle

- Start on login default:
- Needs update check: yes or no
- Needs reinstall action: yes or no
- Needs uninstall action: yes or no
- Needs browser-based help or issue link: yes or no

## 13. Diagnostics

- What should `doctor` validate:
- What should `diag` report:
- What errors should surface in the UI:

## 14. Done means

Release one is done when:

- the tray starts
- the primary window opens
- all listed buttons work
- all listed toggles persist
- all listed links open correctly
- every listed background job reports success or failure clearly