from __future__ import annotations

import pytest

from selfsnap.models import AppConfig, ConfigValidationError, Schedule
from selfsnap.window_sizing import SETTINGS_WINDOW_MIN_HEIGHT, SETTINGS_WINDOW_MIN_WIDTH


def test_duplicate_schedule_ids_are_rejected() -> None:
    config = AppConfig(
        capture_storage_root="C:\\captures",
        archive_storage_root="C:\\archive",
        schedules=[
            Schedule(
                schedule_id="morning",
                label="Morning",
                interval_value=1,
                interval_unit="day",
                start_date_local="2026-03-23",
                start_time_local="09:00:00",
            ),
            Schedule(
                schedule_id="morning",
                label="Morning 2",
                interval_value=1,
                interval_unit="day",
                start_date_local="2026-03-23",
                start_time_local="10:00:00",
            ),
        ],
    )
    with pytest.raises(ConfigValidationError):
        config.validate()


def test_archive_storage_root_is_required() -> None:
    config = AppConfig(capture_storage_root="C:\\captures", archive_storage_root="")
    with pytest.raises(ConfigValidationError):
        config.validate()


def test_scheduler_sync_state_is_validated() -> None:
    config = AppConfig(
        capture_storage_root="C:\\captures",
        archive_storage_root="C:\\archive",
        scheduler_sync_state="broken",
    )
    with pytest.raises(ConfigValidationError):
        config.validate()


def test_storage_preset_is_validated() -> None:
    config = AppConfig(
        capture_storage_root="C:\\captures",
        archive_storage_root="C:\\archive",
        storage_preset="dropbox",
    )
    with pytest.raises(ConfigValidationError):
        config.validate()


def test_settings_window_size_floor_is_validated() -> None:
    config = AppConfig(
        capture_storage_root="C:\\captures",
        archive_storage_root="C:\\archive",
        settings_window_width=SETTINGS_WINDOW_MIN_WIDTH - 1,
        settings_window_height=SETTINGS_WINDOW_MIN_HEIGHT - 1,
    )
    with pytest.raises(ConfigValidationError):
        config.validate()


def test_legacy_schedule_dict_migrates_to_daily_recurrence() -> None:
    schedule = Schedule.from_dict(
        {
            "schedule_id": "morning",
            "label": "Morning",
            "local_time": "09:15",
            "enabled": True,
        }
    )

    assert schedule.interval_value == 1
    assert schedule.interval_unit == "day"
    assert schedule.start_time_local == "09:15:00"


# ---------------------------------------------------------------------------
# AppConfig validation — uncovered branches
# ---------------------------------------------------------------------------


def test_schema_version_mismatch_raises() -> None:
    config = AppConfig(
        capture_storage_root="C:\\captures",
        archive_storage_root="C:\\archive",
        schema_version=1,
    )
    with pytest.raises(ConfigValidationError, match="schema_version"):
        config.validate()


def test_capture_storage_root_empty_raises() -> None:
    config = AppConfig(capture_storage_root="", archive_storage_root="C:\\archive")
    with pytest.raises(ConfigValidationError, match="capture_storage_root"):
        config.validate()


def test_retention_mode_invalid_raises() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        retention_mode="delete_immediately",
    )
    with pytest.raises(ConfigValidationError, match="retention_mode"):
        config.validate()


def test_retention_days_none_when_keep_days_raises() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        retention_mode="keep_days",
        retention_days=None,
    )
    with pytest.raises(ConfigValidationError, match="retention_days"):
        config.validate()


def test_retention_days_zero_when_supplied_raises() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        retention_mode="keep_forever",
        retention_days=0,
    )
    with pytest.raises(ConfigValidationError, match="retention_days"):
        config.validate()


def test_log_level_invalid_raises() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        log_level="WARNING",
    )
    with pytest.raises(ConfigValidationError, match="log_level"):
        config.validate()


def test_settings_window_height_too_small_raises() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        settings_window_height=SETTINGS_WINDOW_MIN_HEIGHT - 1,
    )
    with pytest.raises(ConfigValidationError, match="settings_window_height"):
        config.validate()


def test_slot_match_tolerance_negative_raises() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        slot_match_tolerance_seconds=-1,
    )
    with pytest.raises(ConfigValidationError, match="slot_match_tolerance_seconds"):
        config.validate()


def test_capture_mode_invalid_raises() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        capture_mode="screenshot",
    )
    with pytest.raises(ConfigValidationError, match="capture_mode"):
        config.validate()


def test_image_format_invalid_raises() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        image_format="bmp",
    )
    with pytest.raises(ConfigValidationError, match="image_format"):
        config.validate()


def test_image_quality_out_of_range_raises() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        image_quality=0,
    )
    with pytest.raises(ConfigValidationError, match="image_quality"):
        config.validate()


def test_retention_grace_days_zero_raises() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        retention_grace_days=0,
    )
    with pytest.raises(ConfigValidationError, match="retention_grace_days"):
        config.validate()


# ---------------------------------------------------------------------------
# AppConfig.mark_scheduler_sync_ok
# ---------------------------------------------------------------------------


def test_mark_scheduler_sync_ok_clears_failed_state() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
    )
    config.mark_scheduler_sync_failed("something broke")
    assert config.scheduler_sync_failed() is True

    config.mark_scheduler_sync_ok()
    assert config.scheduler_sync_failed() is False
    assert config.scheduler_sync_message is None


# ---------------------------------------------------------------------------
# AppConfig.get_schedule
# ---------------------------------------------------------------------------


def test_get_schedule_returns_none_for_unknown_id() -> None:
    from selfsnap.models import Schedule

    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        schedules=[
            Schedule(
                schedule_id="morning",
                label="Morning",
                interval_value=1,
                interval_unit="day",
                start_date_local="2026-01-01",
                start_time_local="09:00:00",
            )
        ],
    )
    assert config.get_schedule("evening") is None


# ---------------------------------------------------------------------------
# Schedule validation — uncovered branches
# ---------------------------------------------------------------------------


def test_schedule_invalid_interval_unit_raises() -> None:
    from selfsnap.models import Schedule

    sched = Schedule(
        schedule_id="test",
        label="Test",
        interval_value=1,
        interval_unit="fortnight",
        start_date_local="2026-01-01",
        start_time_local="09:00:00",
    )
    with pytest.raises(ConfigValidationError, match="interval_unit"):
        sched.validate()


def test_schedule_invalid_start_date_raises() -> None:
    from selfsnap.models import Schedule

    sched = Schedule(
        schedule_id="test",
        label="Test",
        interval_value=1,
        interval_unit="day",
        start_date_local="not-a-date",
        start_time_local="09:00:00",
    )
    with pytest.raises(ConfigValidationError, match="start_date_local"):
        sched.validate()


def test_schedule_invalid_start_time_raises() -> None:
    from selfsnap.models import Schedule

    sched = Schedule(
        schedule_id="test",
        label="Test",
        interval_value=1,
        interval_unit="day",
        start_date_local="2026-01-01",
        start_time_local="99:00:00",
    )
    with pytest.raises(ConfigValidationError, match="start_time_local"):
        sched.validate()


def test_schedule_validate_raises_for_invalid_schedule_id() -> None:
    from selfsnap.models import Schedule

    sched = Schedule(
        schedule_id="HAS_UPPER",
        label="Test",
        interval_value=1,
        interval_unit="day",
        start_date_local="2026-01-01",
        start_time_local="09:00:00",
    )
    with pytest.raises(ConfigValidationError, match="schedule_id"):
        sched.validate()


def test_schedule_validate_raises_for_empty_label() -> None:
    from selfsnap.models import Schedule

    sched = Schedule(
        schedule_id="valid_id",
        label="   ",
        interval_value=1,
        interval_unit="day",
        start_date_local="2026-01-01",
        start_time_local="09:00:00",
    )
    with pytest.raises(ConfigValidationError, match="label"):
        sched.validate()


def test_schedule_validate_raises_for_zero_interval_value() -> None:
    from selfsnap.models import Schedule

    sched = Schedule(
        schedule_id="valid_id",
        label="Test",
        interval_value=0,
        interval_unit="day",
        start_date_local="2026-01-01",
        start_time_local="09:00:00",
    )
    with pytest.raises(ConfigValidationError, match="interval_value"):
        sched.validate()
