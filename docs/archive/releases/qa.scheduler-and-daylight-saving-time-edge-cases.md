# QA Note: Scheduler And DST Edge Cases

[ARCHIVED RELEASE]
This file is part of the archived release pack indexed in [README.md](README.md).
It preserves historical release-specific QA guidance and is not the active product or maintainer contract.

This QA note captures the scheduler edge cases and validation strategy that matter most for DST-sensitive and coarse-schedule behavior.

## Hybrid scheduler model

- `seconds` and `minutes`: tray-managed, high-frequency.
- `hours` and above: Windows Task Scheduler one-shot tasks with re-registration.

## Edge cases to account for

- Sleep/wake gaps where scheduled windows are missed.
- DST transitions creating ambiguous or skipped local times.
- Invalid calendar dates for monthly/yearly anchors.
- Global disable while old/stale scheduler entries still exist.

## Expected behavior

- Missed or skipped outcomes are recorded honestly.
- Invalid monthly/yearly anchor dates are skipped rather than silently remapped.
- Scheduler sync failure blocks scheduled capture while keeping manual capture available.
- Coarse tasks should be re-synced after config/schedule changes.

## Validation strategy

- Use time-freezing and recurrence tests for deterministic DST/date edge checks.
- Validate scheduler sync behavior with at least one coarse schedule in Windows Task Scheduler.
- Confirm disabling scheduled capture clears active SelfSnap task registrations.

## Related files

- `docs/archive/releases/common.release-readiness-criteria-v1.0.md`
- `docs/developer/validation-checklist.md`
- `tests/unit/test_recurrence.py`
- `tests/unit/test_recurrence_hypothesis.py`
