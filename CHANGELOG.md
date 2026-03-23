# Changelog

## v0.4.0 - 2026-03-23

Why: The first broad post-v1 stabilization pass closed the most disruptive product and UI regressions.

- Finalized the post-v1 fixes across storage presets, reset behavior, tray state, and runtime launch paths.
- Isolated tray UI state more safely and hardened uninstall fallback behavior.
- Stabilized the settings window after capture-related regressions and expanded UI regression coverage.

## v0.3.0 - 2026-03-22

Why: Source setup and runtime verification became reliable enough for repeated local installs.

- Added a bootstrap setup script for creating a clean development or runtime environment.
- Hardened runtime dependency detection so broken Pillow/runtime states fail clearly.
- Added targeted tests around runtime verification and setup-related behavior.

## v0.2.0 - 2026-03-22

Why: Windows runtime and installation flow became usable end to end.

- Finalized Windows runtime, tray startup, worker packaging readiness, and scheduler integration.
- Aligned documentation with the Windows install and validation flow.
- Expanded automated coverage around archive behavior and scheduler-backed paths.

## v0.1.0 - 2026-03-21

Why: First tested runnable SelfSnap baseline.

- Initial Windows 11 tray app with manual and scheduled screenshot capture.
- Local SQLite metadata, retention handling, and tray control surface.
- Baseline automated coverage for config, retention, and worker flows.
