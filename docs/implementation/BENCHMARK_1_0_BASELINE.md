# SelfSnap 1.0 Baseline Benchmark

## Purpose

This file records the baseline state of SelfSnap at the start of the `1.0` push.
It is a comparison point for later iterations, not a release note.

## Baseline snapshot

- Current repo version: `v0.9.4`
- Product shape: Windows 11-only, local-first screenshot utility for privacy-minded power users
- Runtime boundary: no telemetry, no cloud sync, no stealth behavior, browser-mediated issue reporting only
- Install posture: source-based install is the supported baseline
- Capture contract: recurring schedules, manual capture, composite by default, optional per-monitor output, configurable `png` / `jpeg` / `webp`
- Review surfaces: tray status, recent captures, statistics, latest-record shortcuts

## Current benchmark

| Area | Baseline state | 1.0 target | Current assessment |
|---|---|---|---|
| Product contract | README, PRD, SRS, QA, validation, and sample config are mostly aligned to shipped behavior | One stable public contract across docs and runtime | In progress |
| Trust disclosure | README plus in-product warning in first-run and Settings | Explicit trust boundary in every critical user-facing surface | Baseline established |
| Automated quality gate | Windows CI compile check plus pytest on Python 3.11 and 3.12 with 80% coverage gate | Stable CI plus stronger release-oriented validation | Baseline established |
| Scheduler reliability | Broad recurrence tests exist and scheduler sync is heavily covered | Verified DST, sleep/resume, enable/disable, and calendar-edge behavior | Not yet benchmarked for 1.0 |
| Hardware validation | Headless logic coverage is strong; hardware-dependent capture remains outside normal CI | Repeatable real-device matrix for monitor and DPI variants | Not yet benchmarked for 1.0 |
| Distribution | Source-based install and release-note automation exist | Public release artifacts and deterministic update story | Not yet benchmarked for 1.0 |
| Supportability | Browser-mediated issue reporting and diagnostics exist | Clear recovery and troubleshooting paths for public users | Partial |

## Evidence anchors

- Public contract: `README.md`
- Implementation contract: `docs/implementation/PRD_v1.md`
- Runtime contract: `docs/implementation/SRS_Architecture_v1.md`
- Trust and privacy posture: `docs/implementation/QA_Privacy_v1.md`
- Ship gate: `docs/implementation/RELEASE_CRITERIA_1_0.md`
- Validation surface: `docs/implementation/VALIDATION_CHECKLIST.md`
- Runtime trust messaging: `src/selfsnap/tray/first_run.py`, `src/selfsnap/tray/settings_window.py`, `src/selfsnap/ui_labels.py`
- CI baseline: `.github/workflows/ci.yml`

## Benchmark focus for the next iteration

1. Scheduler correctness at DST and timezone boundaries.
2. Public-release distribution benchmark: build artifacts, update path, reinstall path, rollback expectations.
3. Real-device validation benchmark for multi-monitor and mixed-DPI setups.
4. Supportability benchmark for scheduler-sync failure, storage-root failure, and startup recovery.

## Exit condition for this baseline

This baseline is superseded when SelfSnap has a release-candidate benchmark that measures the same areas against the `1.0` go / no-go gate.