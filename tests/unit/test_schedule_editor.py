from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest

from selfsnap.models import ConfigValidationError, Schedule
from selfsnap.tray.schedule_editor import (
    default_draft,
    default_unit_label,
    draft_from_form,
    draft_from_schedule,
    draft_to_schedule,
    editor_selection_summary,
    enabled_label,
    first_run_schedule_help_text,
    generate_schedule_id,
    normalize_draft,
    schedule_help_text,
    schedules_summary_text,
    selection_state,
    unit_label,
    unit_labels,
    unit_phrase,
    unit_value,
)


def test_schedule_help_text_mentions_defaults_and_multi_select() -> None:
    text = schedule_help_text()

    assert "Every N seconds, minutes, hours, days, weeks, months, or years" in text
    assert "Defaults are Every 1 day, today, and now" in text
    assert "select many rows to delete only" in text
    assert "click Status to pause or resume a schedule" in text
    assert "month/year schedules skip invalid dates" in text


def test_first_run_schedule_help_text_points_to_settings() -> None:
    text = first_run_schedule_help_text()

    assert "Settings > Schedules" in text
    assert "Every N seconds, minutes, hours, days, weeks, or years" not in text
    assert "Every N seconds, minutes, hours, days, weeks, months, or years" in text
    assert "Defaults are Every 1 day, today, and now" in text


def test_unit_labels_round_trip() -> None:
    assert default_unit_label() == "Days"
    assert unit_labels() == ["Seconds", "Minutes", "Hours", "Days", "Weeks", "Months", "Years"]
    assert unit_value("Days") == "day"
    assert unit_label("day") == "Days"
    assert unit_phrase(1, "day") == "day"
    assert unit_phrase(3, "day") == "days"


def test_selection_state_controls_editor_modes() -> None:
    add_state = selection_state(0)
    single_state = selection_state(1)
    multi_state = selection_state(2)

    assert add_state.mode == "add"
    assert add_state.add_enabled is True
    assert add_state.fields_enabled is True

    assert single_state.mode == "single"
    assert single_state.save_enabled is True
    assert single_state.cancel_enabled is True
    assert single_state.delete_enabled is True

    assert multi_state.mode == "multi"
    assert multi_state.add_enabled is False
    assert multi_state.save_enabled is False
    assert multi_state.cancel_enabled is False
    assert multi_state.delete_enabled is True
    assert multi_state.fields_enabled is False


def test_editor_selection_summary_tracks_editor_mode() -> None:
    assert editor_selection_summary(0).startswith("Add a new recurring capture")
    assert editor_selection_summary(1).startswith("Editing one schedule")
    assert editor_selection_summary(3).startswith("3 schedules selected")


def test_enabled_label_uses_clear_status_words() -> None:
    assert enabled_label(True) == "Enabled"
    assert enabled_label(False) == "Paused"


def test_schedules_summary_text_reports_enabled_count_and_anchor() -> None:
    first = draft_from_form(
        label="Daily",
        interval_value="1",
        unit_label_value="Days",
        start_date="2026-03-23",
        start_time="08:15",
        enabled=True,
    )
    second = draft_from_form(
        label="Nightly",
        interval_value="1",
        unit_label_value="Days",
        start_date="2026-03-22",
        start_time="23:45",
        enabled=False,
    )

    text = schedules_summary_text([first, second])

    assert text.startswith("1 of 2 schedules enabled")
    assert "2026-03-23 08:15" in text


def test_schedules_summary_text_handles_empty_and_all_paused() -> None:
    assert schedules_summary_text([]).startswith("No recurring captures configured")

    paused = draft_from_form(
        label="Paused",
        interval_value="15",
        unit_label_value="Minutes",
        start_date="2026-03-21",
        start_time="06:30",
        enabled=False,
    )

    text = schedules_summary_text([paused])

    assert text.startswith("All 1 schedules are paused")
    assert "2026-03-21 06:30" in text


def test_default_draft_uses_every_one_day_now() -> None:
    draft = default_draft(datetime(2026, 3, 23, 9, 15, 45))

    assert draft.interval_value == 1
    assert draft.interval_unit == "day"
    assert draft.start_date_local.isoformat() == "2026-03-23"
    assert draft.start_time_local.strftime("%H:%M:%S") == "09:15:45"
    assert draft.schedule_id is None


def test_draft_round_trips_to_schedule_and_back() -> None:
    draft = draft_from_form(
        label="Morning",
        interval_value="5",
        unit_label_value="Minutes",
        start_date="2026-03-23",
        start_time="14:30",
        enabled=True,
    )

    schedule = draft_to_schedule(draft)

    assert isinstance(schedule, Schedule)
    assert schedule.interval_value == 5
    assert schedule.interval_unit == "minute"
    assert schedule.start_date_local == "2026-03-23"
    assert schedule.start_time_local == "14:30:00"
    assert schedule.schedule_id.startswith("sched_")

    round_tripped = draft_from_schedule(schedule, datetime(2026, 3, 23, 9, 0, 0))
    assert round_tripped.label == "Morning"
    assert round_tripped.interval_value == 5
    assert round_tripped.interval_unit == "minute"
    assert round_tripped.start_date_local.isoformat() == "2026-03-23"
    assert round_tripped.start_time_local.strftime("%H:%M:%S") == "14:30:00"
    assert round_tripped.schedule_id == schedule.schedule_id


def test_legacy_schedule_falls_back_to_daily_defaults() -> None:
    legacy_schedule = SimpleNamespace(
        schedule_id="legacy_schedule",
        label="Legacy",
        enabled=False,
        local_time="08:15",
    )

    draft = draft_from_schedule(legacy_schedule, datetime(2026, 3, 23, 9, 0, 0))

    assert draft.label == "Legacy"
    assert draft.enabled is False
    assert draft.interval_value == 1
    assert draft.interval_unit == "day"
    assert draft.start_date_local.isoformat() == "2026-03-23"
    assert draft.start_time_local.strftime("%H:%M:%S") == "08:15:00"
    assert draft.schedule_id == "legacy_schedule"


def test_normalize_draft_rejects_blank_label() -> None:
    draft = default_draft(datetime(2026, 3, 23, 9, 0, 0))
    draft.label = "   "

    with pytest.raises(ConfigValidationError, match="label must not be empty"):
        normalize_draft(draft)


def test_generate_schedule_id_returns_internal_identifier() -> None:
    schedule_id = generate_schedule_id()

    assert schedule_id.startswith("sched_")
    assert len(schedule_id) > len("sched_")
