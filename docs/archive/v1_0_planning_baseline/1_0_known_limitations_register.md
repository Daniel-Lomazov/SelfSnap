# SelfSnap 1.0 Known Limitations Register

Last updated: 2026-03-29
Baseline: v0.9.4

This register lists limitations accepted for 1.0 with impact, mitigation, disclosure, and roadmap signal.

## L1 - No encryption at rest

Description: Captures are stored as standard image files without encryption.

User impact: If storage is accessible to other users/processes, captures are readable.

Mitigation/disclosure:
- `src/selfsnap/ui_labels.py` `local_privacy_notice()` in first-run and Settings
- `README.md` privacy warning
- `docs/archive/releases/common.release-readiness-criteria-v1.0.md` explicit limitation

Post-1.0 signal: Maybe (demand-gated, requires key-management design).

## L2 - Wake-from-sleep is best effort

Description: Resume timing can produce missed scheduled slots; no strict guarantee.

User impact: Missed captures may occur through sleep/wake transitions.

Mitigation/disclosure:
- Reconcile loop records missed slots explicitly
- Task Scheduler wake behavior used where available
- Limitation documented in release criteria

Post-1.0 signal: No major architectural change planned.

## L3 - No guarantee during full shutdown/logged-out states

Description: Captures require logged-in desktop context.

User impact: Schedules during shutdown/logged-out windows are missed.

Mitigation/disclosure: Product contract explicitly defines logged-in desktop session requirements.

Post-1.0 signal: No (would require service architecture and trust-model change).

## L4 - Windows 11 only

Description: Product supports Windows 11 only.

User impact: Unsupported on Windows 10, macOS, Linux.

Mitigation/disclosure: Repeated in README and release criteria.

Post-1.0 signal: No cross-platform roadmap commitment.

## L5 - Locked-session behavior is platform-constrained

Description: Locked-session capture reliability depends on Windows session semantics.

User impact: Some captures may fail in locked-session states.

Mitigation/disclosure: Failures are recorded with explicit outcomes; QA docs call out locked-session testing.

Post-1.0 signal: No planned architecture shift.

## L6 - No cloud sync/remote backup

Description: Local-first only; no remote sync service.

User impact: Local storage loss may mean data loss.

Mitigation/disclosure: OneDrive preset exists as local-path option; no app-managed remote sync.

Post-1.0 signal: No cloud-sync roadmap commitment.

## L7 - No enterprise deployment model

Description: No MDM/group policy/institutional deployment strategy.

User impact: Enterprise managed environments may not support deployment.

Mitigation/disclosure: Product position is personal utility for power users.

Post-1.0 signal: No.

## L8 - No full history browser/search UI

Description: Only lightweight recent and stats surfaces are provided.

User impact: Deep historical exploration requires file explorer/manual workflows.

Mitigation/disclosure: Deferred in PRD; date-structured storage paths aid manual browsing.

Post-1.0 signal: Yes.

## L9 - Source-based install only

Description: Installation relies on source checkout plus PowerShell scripts.

User impact: Non-technical users face higher setup friction.

Mitigation/disclosure: README quick-start and scripts are maintained; audience remains technical.

Post-1.0 signal: Yes (packaged installer candidate).

## L10 - Browser-mediated issue reporting only

Description: App opens a browser issue template; no in-app issue submission.

User impact: Requires user interaction and usually a GitHub account.

Mitigation/disclosure: This is intentional to preserve user control and avoid automatic data submission.

Post-1.0 signal: No model change planned; possible convenience improvements only.
