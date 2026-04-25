from __future__ import annotations

from datetime import UTC, datetime

from selfsnap.models import CaptureRecord

from selfsnap.tray.settings_window import (
    SCHEDULE_TREE_COLUMN_SPECS,
    capture_record_visual_state,
    resolve_schedule_tree_column_widths,
    should_refresh_polled_latest_record,
    should_sync_polled_app_enabled,
    use_stacked_schedule_layout,
)


def _record(
    *,
    record_id: str = "record-1",
    outcome_code: str = "capture_saved",
    outcome_category: str = "success",
    file_present: bool = True,
) -> CaptureRecord:
    now = datetime(2026, 4, 25, 12, 0, 0, tzinfo=UTC).isoformat()
    return CaptureRecord(
        record_id=record_id,
        trigger_source="manual",
        schedule_id=None,
        planned_local_ts=None,
        started_utc=now,
        finished_utc=now,
        outcome_category=outcome_category,
        outcome_code=outcome_code,
        image_path="C:\\captures\\cap.png",
        file_present=file_present,
        image_sha256="abc",
        monitor_count=1,
        composite_width=10,
        composite_height=10,
        file_bytes=10,
        error_code=None,
        error_message=None,
        archived=False,
        archived_at_utc=None,
        retention_deleted_at_utc=None,
        app_version="1.3.1",
        created_utc=now,
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


def test_capture_record_visual_state_is_none_without_a_record() -> None:
    assert capture_record_visual_state(None) is None


def test_should_refresh_polled_latest_record_when_new_record_arrives() -> None:
    assert (
        should_refresh_polled_latest_record(
            current_record=_record(record_id="record-1"),
            disk_record=_record(record_id="record-2"),
        )
        is True
    )


def test_should_refresh_polled_latest_record_when_same_record_changes_visually() -> None:
    assert (
        should_refresh_polled_latest_record(
            current_record=_record(outcome_code="capture_started", outcome_category="running", file_present=False),
            disk_record=_record(outcome_code="capture_saved", outcome_category="success", file_present=True),
        )
        is True
    )


def test_should_not_refresh_polled_latest_record_when_visual_state_is_unchanged() -> None:
    current = _record()

    assert (
        should_refresh_polled_latest_record(
            current_record=current,
            disk_record=_record(),
        )
        is False
    )
