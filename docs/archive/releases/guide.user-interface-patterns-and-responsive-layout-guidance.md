# Guide: UI Patterns And Responsive Layout

[ARCHIVED RELEASE]
This file is part of the archived release pack indexed in [README.md](README.md).
It preserves historical release-specific guide material and is not the active product or maintainer contract.

This guide captures the stable UI behavior conventions for the Fluent-style Settings experience.

## Scope

This guide focuses on the layout, interaction, and validation rules that should remain stable during future UI iteration.

## Core layout thresholds

- `STACKED_COMPACT_LAYOUT_MAX_WIDTH = 660` controls stacked behavior in schedule panel composition.
- `RESPONSIVE_CARD_SPLIT_MIN_WIDTH = 820` controls stacked vs split behavior for major card grids.
- Width transitions must keep controls reachable without hidden actions.

## Settings surface composition

- Primary tabs: `General`, `Storage`, `Schedules`, `Diagnostics`, `Maintenance`.
- Card/inset building is centralized through `src/selfsnap/ui/fluent.py` helpers.
- Text-heavy summaries use dynamic wrapping to prevent clipping during resize.

## Schedule panel rules

- Narrow widths: list panel and editor panel stack vertically.
- Wider widths: list/editor split into side-by-side equal-weight columns.
- Tree columns use heading + cell measurement to autofit values after refresh and configure events.

## UX regression risks

- Layout jitter during rapid resize events.
- Truncated schedule fields after add/save/delete flows.
- Hidden action buttons on narrow widths.

## Validation hooks

- Verify both threshold crossings during manual resize.
- Verify Schedules tab remains keyboard/mouse accessible in both modes.
- Verify Diagnostics cards remain readable in stacked and split states.
