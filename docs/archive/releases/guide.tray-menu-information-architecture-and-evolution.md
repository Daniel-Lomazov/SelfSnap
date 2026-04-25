# Guide: Tray Menu Information Architecture And Evolution

[ARCHIVED RELEASE]
This file is part of the archived release pack indexed in [README.md](README.md).
It preserves historical release-specific guide material and is not the active product or maintainer contract.

This guide preserves the tray command surface and the rationale behind the current grouping, wording, and supportability expectations.

## Purpose

Preserve the tray command surface and the rationale for current grouping and wording.

## Current menu intent

- Keep high-frequency actions (`Capture Now`, settings access, schedule enable/disable) obvious.
- Separate browsing/status actions from lifecycle actions (reinstall/update/uninstall/restart/exit).
- Keep issue reporting and diagnostics easy to discover without exposing sensitive local data.

## Stable behavior expectations

- Exactly one active tray instance should own menu interactions.
- Menu labels should reflect current app state (enabled/disabled, scheduler warnings, latest capture summary).
- Tray action handlers must not block the tray thread for long-running operations.

## Iteration themes behind current design

- Duplicate icon and duplicate action regressions required stronger single-instance/runtime hygiene.
- Users needed clearer grouping to avoid accidental destructive/lifecycle actions.
- Support workflows benefited from keeping diagnostics and report-entry paths near top-level actions.

## Documentation requirements

- Public docs must describe where users find capture, settings, diagnostics, and lifecycle actions.
- Troubleshooting docs must include duplicate-tray remediation and restart expectations.
