from __future__ import annotations

from selfsnap.tray.settings_window import (
    SCHEDULE_TREE_COLUMN_SPECS,
    resolve_schedule_tree_column_widths,
    should_sync_polled_app_enabled,
    use_stacked_schedule_layout,
)


def test_schedule_tree_column_widths_preserve_minimums_when_narrow() -> None:
    widths = resolve_schedule_tree_column_widths(320)

    assert widths == {
        name: minimum for name, minimum, _weight, _anchor in SCHEDULE_TREE_COLUMN_SPECS
    }


def test_schedule_tree_column_widths_expand_to_fill_available_width() -> None:
    widths = resolve_schedule_tree_column_widths(900)

    assert sum(widths.values()) == 900
    assert widths["recurrence"] > widths["label"]
    assert widths["start"] > 128
    assert widths["enabled"] == 72


def test_use_stacked_schedule_layout_switches_at_compact_threshold() -> None:
    assert use_stacked_schedule_layout(660) is True
    assert use_stacked_schedule_layout(661) is False


def test_should_sync_polled_app_enabled_when_local_value_is_clean() -> None:
    assert (
        should_sync_polled_app_enabled(
            current_ui_value=False,
            saved_value=False,
            disk_value=True,
            local_dirty=False,
        )
        is True
    )


def test_should_not_sync_polled_app_enabled_over_unsaved_local_change() -> None:
    assert (
        should_sync_polled_app_enabled(
            current_ui_value=True,
            saved_value=False,
            disk_value=False,
            local_dirty=True,
        )
        is False
    )


def test_should_sync_polled_app_enabled_after_local_value_returns_to_saved_state() -> None:
    assert (
        should_sync_polled_app_enabled(
            current_ui_value=False,
            saved_value=False,
            disk_value=True,
            local_dirty=True,
        )
        is True
    )
