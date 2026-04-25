# SelfSnap Win11 Product Requirements (Maintainer Contract)

This maintainer doc captures the active product contract for the current repo state.

## Goal

Ship a Windows 11-only, local-first screenshot utility that is transparent, user-controlled, and reliable for recurring desktop capture workflows.

## Product principles

- Local-first by default: captures and metadata remain on local storage unless the user explicitly chooses network-driven actions.
- Honest status: success, failure, missed, and skipped outcomes are surfaced consistently in UI, logs, and DB metadata.
- User control over automation: users can globally pause scheduling, pause individual schedules, and review diagnostics before changing state.
- Predictable operations: install/update/reinstall/uninstall/reset flows are explicit and reversible where possible.

## Must-have behavior

- Manual capture works from tray and CLI.
- Recurring schedules support `seconds`, `minutes`, `hours`, `days`, `weeks`, `months`, and `years`.
- High-frequency schedules are tray-managed; coarse schedules are Windows Task Scheduler-backed.
- Missed scheduled slots are represented honestly in metadata/reconciliation behavior.
- Scheduled capture remains blocked until first-run completion.
- Capture output supports `composite` capture and `per_monitor` capture (one image per monitor).
- Image output supports `png`, `jpeg`, and `webp`; quality controls apply to `jpeg` and `webp`.
- Settings exposes storage, retention, capture output, schedules, diagnostics, and maintenance controls.
- Tray actions cover capture, settings, diagnostics-related flows, lifecycle actions, and issue reporting.

## Current maintained scope notes

- Fluent-style Settings surface with responsive card and panel behavior.
- Schedule editor/list layout tuning with auto-fit columns and narrow-width stacking behavior.
- Expanded diagnostics surface and clearer supportability signals in Settings/tray.
- Runtime launch hardening for source installs through checkout-local `.venv` interpreter enforcement.
- Better state sync protections to avoid clobbering unsaved local Settings edits.
- Console-free background launch behavior for tray/worker flows.
- Browser-mediated issue reporting with safe diagnostics and no automatic sensitive attachments.

## Reset scope

- Deletes SelfSnap-managed captures and archive files.
- Clears config, DB history, and logs under `%LOCALAPPDATA%\SelfSnap`.
- Removes startup shortcut and SelfSnap scheduled capture tasks.
- Returns runtime to first-run onboarding.
- Does not uninstall the app package or repository checkout.

## Deferred / non-goals

- Full history browser and search UI.
- Cross-platform support.
- Encryption at rest.
- Cloud sync and remote telemetry.
