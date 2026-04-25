# SelfSnap 1.0 Gap Register

Last updated: 2026-03-29
Baseline: v0.9.4

Priority definitions:
- P0: Must close before 1.0 ship.
- P1: Should close before ship; defer only with explicit recorded decision.
- P2: Accepted post-1.0 gap.

## P0 Gaps - Must Close Before Ship

| ID | Area | Description | Current State | 1.0 Requirement | Closure Signal |
|---|---|---|---|---|---|
| P0-1 | Hardware validation | Validation checklist has not been executed and recorded on real hardware | Marked not benchmarked | Full checklist run with dated machine notes and exception annotations | `docs/archive/releases/release_history.md` updated with execution evidence |
| P0-2 | Distribution | No GitHub Release exists for updater to consume | Source install only | Create tagged GitHub Release with source artifact and notes | Updater sees expected latest tag |
| P0-3 | Lifecycle path verification | Clean-machine install/reinstall/uninstall/update not recorded | Test steps exist, run evidence missing | Execute and record clean-machine lifecycle path | Included in checklist execution evidence |
| P0-4 | Scheduler correctness evidence | DST-sensitive failures possible if unresolved | Tests exist, must be proven green | Full pytest run passes with no unresolved scheduler failures | Dated passing run in CI or local evidence |
| P0-5 | Runtime UI verification | Recent Captures and Statistics are in scope but not strongly automated | Shipped by contract, limited automated behavioral proof | Verify both windows open and display real data without crash | Hardware checklist evidence includes this verification |
| P0-6 | Release notes accuracy | CHANGELOG may lag code at tag time | v0.9.4 current baseline | Update changelog for all 1.0-bound deltas before tag | Changelog entry finalized before release creation |
| P0-7 | Contract coherence | Public/runtime/implementation docs may drift | In progress baseline | Final coherence pass across README, PRD, SRS, QA, sample config, UI text | Spot-check complete with any drifts fixed |

## P1 Gaps - Should Close Before Ship

| ID | Area | Description | Current State | 1.0 Requirement | Closure Signal |
|---|---|---|---|---|---|
| P1-1 | README troubleshooting | No dedicated troubleshooting section | Missing | Add concise troubleshooting section with diag/doctor and issue flow | README contains troubleshooting guidance |
| P1-2 | Scheduler-sync UX | Failure states may not always provide clear next action | Partial | Ensure warning path is explicit and actionable | Verified user-facing message and recovery steps |
| P1-3 | OneDrive edge-case docs | Recovery behavior for missing OneDrive root under-documented | Partial | Add operator-facing recovery note | README or checklist includes OneDrive recovery guidance |
| P1-4 | Wake/sleep disclosure breadth | Limitation is in release criteria but may be under-surfaced | Partial | Ensure known limitation is visible in public-facing docs | README known limitations includes wake/sleep behavior |

## P2 Gaps - Accepted Post-1.0

| ID | Area | Description | Post-1.0 Signal |
|---|---|---|---|
| P2-1 | Hardware DST transition exercise | Real transition-window runtime test | Keep as roadmap validation hardening |
| P2-2 | Mixed-DPI multi-monitor matrix | Broader real-device coverage | Keep as reliability hardening |
| P2-3 | Packaged installer | Signed .exe/.msi/MSIX distribution | Candidate if broader audience demand appears |
| P2-4 | Auto-update installer flow | Download/install without manual git steps | Candidate after distribution expansion |
| P2-5 | History browser/search UX | Rich browsing, filtering, search | Explicitly deferred in PRD |
| P2-6 | Encryption at rest | At-rest crypto with key-management strategy | Demand-gated roadmap item |
| P2-7 | Expanded support docs | FAQ and deeper troubleshooting corpus | Operational maturity improvement |

## Recommended P0 Closure Order

1. P0-4: run full pytest and eliminate unresolved failures.
2. P0-7: perform final contract coherence pass.
3. P0-1/P0-3/P0-5: run full hardware validation session and record evidence.
4. P0-2: create release tag and release notes.
5. P0-6: finalize changelog immediately before tagging.
