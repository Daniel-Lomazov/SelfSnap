# SelfSnap Issue Reporting

## User-facing flow

- `Report Issue` is available from the tray menu.
- It is the default tray action where the Windows shell honors pystray default activation.
- The dialog collects a short user paragraph plus an optional safe-diagnostics toggle.
- The same reporting flow must remain accessible even when Settings is open.

## Privacy boundary

- SelfSnap is offline by default.
- SelfSnap never uploads screenshots automatically.
- SelfSnap never attaches local file paths, logs, or database contents automatically.
- Safe diagnostics are limited to product/runtime metadata such as app version, storage preset, scheduler sync state, and latest outcome code.
- Final GitHub submission is always user-controlled in the browser.
- No silent upload or background network activity happens during issue reporting.

## Submission mode

- Browser mode:
  - only mode
  - opens a prefilled GitHub issue page in the browser
  - uses `.github/ISSUE_TEMPLATE/report_issue.md`

## Safe diagnostics fields

Permitted diagnostics summary fields include:

- app version
- storage preset token
- scheduler sync state
- latest outcome code
- limited runtime context required for debugging launch/scheduler issues

Never include by default:

- screenshot files or pixel data
- local absolute file paths that reveal user directory details
- raw DB dumps or log attachments
- capture metadata beyond the minimal summary needed for triage

## GitHub-side preprocessing

- `.github/workflows/issue-intake.yml` parses stable markers from submitted issue bodies.
- It applies area/source/impact labels and posts a planning starter comment marked with `<!-- selfsnap-planning-intake -->`.
- That comment is the intended handoff surface for the next maintainer planning pass.
