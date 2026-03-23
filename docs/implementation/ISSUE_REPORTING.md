# SelfSnap Issue Reporting

## User-facing flow

- `Report Issue` is available from the tray menu.
- It is the default tray action where the Windows shell honors pystray default activation.
- The dialog collects a short user paragraph plus an optional safe-diagnostics toggle.

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

## GitHub-side preprocessing

- `.github/workflows/issue-intake.yml` parses stable markers from submitted issue bodies.
- It applies area/source/impact labels and posts a planning starter comment marked with `<!-- selfsnap-planning-intake -->`.
- That comment is the intended handoff surface for the next maintainer planning pass.
