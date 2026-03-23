# SelfSnap Issue Reporting

## User-facing flow

- `Report Issue` is available from the tray menu.
- It is the default tray action where the Windows shell honors pystray default activation.
- The dialog collects a short user paragraph plus an optional safe-diagnostics toggle.

## Privacy boundary

- SelfSnap never uploads screenshots automatically.
- SelfSnap never attaches local file paths, logs, or database contents automatically.
- Safe diagnostics are limited to product/runtime metadata such as app version, storage preset, scheduler sync state, and latest outcome code.
- Final GitHub submission remains user-controlled unless the user has explicitly configured a GitHub token in the environment.

## Submission modes

- Browser mode:
  - default for any user
  - opens a prefilled GitHub issue page in the browser
  - uses `.github/ISSUE_TEMPLATE/report_issue.md`
- API mode:
  - enabled only when `SELFSNAP_GITHUB_TOKEN`, `GH_TOKEN`, or `GITHUB_TOKEN` is present
  - creates the issue directly through the GitHub issues API
  - still relies on GitHub-side issue intake for labeling and planning prep

## GitHub-side preprocessing

- `.github/workflows/issue-intake.yml` parses stable markers from submitted issue bodies.
- It applies area/source/impact labels and posts a planning starter comment marked with `<!-- selfsnap-planning-intake -->`.
- That comment is the intended handoff surface for the next local-agent planning session.
