# Scheduler and DST Edge Cases

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
