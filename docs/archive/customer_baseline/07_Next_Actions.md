# 07 — Proposed Next Actions for Team

[ARCHIVED BASELINE]
This file is part of the original customer baseline pack preserved in [README.md](README.md).
It is historical reference material and not the active product or maintainer contract.

This file is a short handoff note to a delivery team.

## Immediate next actions

1. Review the first five customer documents for contradictions.
2. Extract explicit must-haves, preferences, and open questions.
3. Draft a lean PRD for a Windows 11 MVP.
4. Draft an SRS covering scheduling, capture, storage, status, and control behavior.
5. Produce an architecture proposal with at least one alternative path.
6. Call out the riskiest unknowns early.
7. Propose a versioned delivery plan:
   - internal proof of concept,
   - usable MVP,
   - personal release candidate.

## Questions the team should answer early

- What is the cleanest Windows 11 execution model for reliable scheduled capture?
- What capture failure states can be distinguished honestly?
- What is the minimum useful control surface?
- What is the smallest set of outputs that still gives real value?
- What should be deferred to protect the MVP?

## Suggested delivery framing

### Phase 1
Manual working prototype proving the capture and storage pipeline.

### Phase 2
Scheduled MVP with local metadata and transparent control.

### Phase 3
Personal release candidate with retention, packaging, and acceptance testing.

## What should not happen next

- Do not expand into cross-platform planning yet.
- Do not overbuild analytics.
- Do not hide unresolved privacy questions.
- Do not hard-freeze technical choices before reviewing alternatives.
