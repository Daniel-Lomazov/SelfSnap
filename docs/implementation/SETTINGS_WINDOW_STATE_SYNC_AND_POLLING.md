# Settings Window State Sync and Polling

## Purpose

Document how Settings keeps local unsaved state coherent while polling disk config for external changes.

## Key model

- UI owns local editable state.
- Polling reads disk config at intervals.
- Sync applies only when local state is not dirty relative to the last saved baseline.

## Critical protection rule

Do not overwrite unsaved local checkbox edits with polled disk values.

This is enforced via:

- saved baseline value tracking
- local dirty flag tracking
- selective sync rule for externally changed config values

## Known regression class

- User toggles schedule enable in Settings but has not clicked Save.
- Background poll sees stale disk value and writes it into UI.
- User loses local change unintentionally.

The branch fix prevents this clobber path.

## Validation

- Toggle enable in Settings without saving while external state changes.
- Confirm local unsaved change remains visible.
- Save and confirm baseline updates, dirty flag clears, and subsequent polling is safe.
