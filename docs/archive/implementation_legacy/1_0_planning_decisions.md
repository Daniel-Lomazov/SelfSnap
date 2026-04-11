# SelfSnap 1.0 Planning Decisions

Last updated: 2026-03-29
Baseline: v0.9.4

## Part 1 - The 10 Blocking Questions

Each question has: (a) recommendation, (b) evidence, (c) caveats.

### Q1 - Audience boundary: Personal 1.0 or public 1.0?

Recommendation: Public 1.0. Anyone can install from the GitHub Release page.

Evidence:
- `README.md` states "Working toward a public 1.0 release for privacy-minded Windows power users."
- `docs/implementation/RELEASE_CRITERIA_1_0.md` defines the audience as an explicit external user class.
- `src/selfsnap/update_checker.py` queries `api.github.com/repos/{repo}/releases/latest`, which is useful only when a public GitHub Release exists.
- `.github/ISSUE_TEMPLATE/report_issue.md` and `.github/ISSUE_TEMPLATE/feature_request.md` are designed for external contributors.

Caveats: "Public" means available on GitHub for a narrow self-selecting audience, not mass-market.

### Q2 - Distribution model: GitHub Releases with assets, or source-install only?

Recommendation: GitHub-tagged release with a source archive (.zip) and CHANGELOG excerpt in the release body. No compiled .exe, no wheel, no PyPI for 1.0.

Evidence:
- `src/selfsnap/update_checker.py` calls `fetch_latest_release_tag()`. Without a GitHub Release with `tag_name`, update checks are inert.
- `docs/implementation/VALIDATION_CHECKLIST.md` requires testing tray "Check for Updates" against a newer tagged release.
- `scripts/install.ps1` already handles source install complexity for the intended audience.

Caveats: A compiled installer adds scope and trust work (signing, packaging, Defender false-positive handling) not warranted for this 1.0.

### Q3 - Validation gate rigor: Does gate #6 hard-block the release?

Recommendation: Yes, gate #6 blocks ship. Passing means full checklist execution on real Windows 11 hardware with date, machine model, and exception notes recorded in `docs/implementation/VALIDATION_CHECKLIST.md`.

Evidence:
- Checklist scenarios are hardware-dependent and not CI-coverable: mixed monitors, DPI, sleep/resume, Task Scheduler behavior.
- Gate #6 in `docs/implementation/RELEASE_CRITERIA_1_0.md` is explicit.
- `docs/implementation/BENCHMARK_1_0_BASELINE.md` marks hardware validation as not yet benchmarked.

Caveats: Specific checklist failures may be accepted only if explicitly documented as known limitations.

### Q4 - DST risk posture: Hard blocker or accepted known limitation?

Recommendation: Conditional hard blocker. If `pytest` is fully green with no DST-related failures, code-level coverage is the 1.0 bar. Any active DST test failure at ship time is P0.

Evidence:
- `tests/unit/test_scheduler_sync.py`, `tests/unit/test_recurrence.py`, and `tests/unit/test_recurrence_hypothesis.py` provide layered scheduler coverage.
- Coarse schedules are delegated to Windows Task Scheduler.
- Repo memory already notes DST sensitivity around `test_build_desired_tasks_includes_enabled_schedules`.

Caveats: Hardware testing exactly across a DST transition is post-1.0 unless an active failure appears.

### Q5 - Trust disclosure surface: In-product sufficient, or does install need it too?

Recommendation: First-run + Settings + README is sufficient for 1.0. Install script disclosure is not required.

Evidence:
- `src/selfsnap/ui_labels.py` provides canonical `local_privacy_notice()` text and it is displayed in `src/selfsnap/tray/first_run.py` and `src/selfsnap/tray/settings_window.py`.
- `README.md` includes a dedicated privacy warning.
- `docs/implementation/QA_Privacy_v1.md` requires first-run and Settings disclosure.

Caveats: If distribution changes to a GUI installer later, disclosure must be revisited there.

### Q6 - Encryption posture: Permanent limitation or post-1.0 roadmap?

Recommendation: Accepted known limitation for 1.0. Post-1.0 roadmap signal is "maybe" based on demand.

Evidence:
- `docs/implementation/RELEASE_CRITERIA_1_0.md` lists no encryption at rest under invariants, known limitations, and out-of-scope.
- In-product trust copy and README disclosure already include this boundary.
- Secure key-management choices require separate design work.

Caveats: Track demand through issues before committing to implementation.

### Q7 - Update mechanism: In-tray notification or GitHub Releases page only?

Recommendation: Keep current in-tray check flow for 1.0. No auto-download or auto-install.

Evidence:
- `src/selfsnap/update_checker.py` implements release fetch and version comparison.
- `docs/implementation/VALIDATION_CHECKLIST.md` includes update-path validation.
- `CHANGELOG.md` v0.9.4 documents git-based update behavior.

Caveats: Users with non-git source archives may need manual refresh steps.

### Q8 - Supportability floor: What is the minimum for a public 1.0?

Recommendation:
1. `selfsnap diag` and `selfsnap doctor` work end-to-end.
2. README includes troubleshooting guidance for issue filing.
3. Browser-mediated issue reporting works from tray.
4. `CHANGELOG.md` is current at tag time.
5. Validation checklist is discoverable from README.

Evidence:
- Diagnostics and issue reporting are implemented and documented.
- Existing issue templates support structured reporting.
- README currently lacks a dedicated troubleshooting section, making this a remaining supportability gap.

Caveats: Dedicated long-form docs can be post-1.0.

### Q9 - Scope lock: Any features above the completion line that should be cut?

Recommendation: No feature cuts. Keep current shipped scope and explicitly verify Recent Captures and Statistics windows before tag.

Evidence:
- `docs/implementation/PRD_v1.md` lists both as shipped scope additions.
- Automated UI coverage for those windows is limited; hardware validation must confirm runtime behavior.

Caveats: Minimal-but-functional behavior is acceptable for 1.0.

### Q10 - Quality bar: Is 80% + mypy + ruff sufficient?

Recommendation: Yes. Keep current gate: CI on 3.11/3.12, coverage >= 80%, mypy clean, ruff clean, plus completed hardware validation checklist.

Evidence:
- Baseline doc positions release hardening around hardware validation, not a higher coverage target.
- Coverage exclusions already isolate hardware/UI surfaces that are poor candidates for strict unit coverage.

Caveats: Spot-check critical modules for local weak coverage pockets even if aggregate passes.

## Part 2 - 7 Decision Dimensions

| Dimension | Decision | Rationale |
|---|---|---|
| Audience boundary | Public 1.0 for privacy-minded Windows 11 power users | Product docs and update mechanism already imply public availability |
| Distribution model | GitHub-tagged release plus source archive and release notes | Matches current install/update architecture and audience |
| Validation gate | Gate #6 hard-blocks ship | Real-device behavior is core risk surface |
| DST risk | Green tests required to ship; active DST failure is P0 | Existing test depth is strong but failure cannot be ignored |
| Trust disclosure | README + first-run + Settings is sufficient | Contract already aligned in docs and runtime |
| Encryption posture | Accepted 1.0 limitation, demand-gated later | Explicitly documented and disclosed today |
| Update mechanism | Manual user-initiated check in tray | Aligns with offline-by-default trust model |

## Part 3 - Scope Lock Statement

Locked IN: Everything in `docs/implementation/RELEASE_CRITERIA_1_0.md` Supported 1.0 contract and `docs/implementation/PRD_v1.md` Must-have and Current shipped scope additions.

Locked OUT: Everything in `docs/implementation/PRD_v1.md` Deferred and `docs/implementation/RELEASE_CRITERIA_1_0.md` Out of scope.

No new scope after this document is committed. Any scope change requires explicit decision-record update with rationale and impact statement.
