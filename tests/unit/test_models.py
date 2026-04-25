from __future__ import annotations

import pytest

from selfsnap.models import AppConfig, ConfigValidationError, Schedule
from selfsnap.window_sizing import SETTINGS_WINDOW_MIN_HEIGHT, SETTINGS_WINDOW_MIN_WIDTH
from tests.support.factories import make_app_config, make_schedule


def test_duplicate_schedule_ids_are_rejected() -> None:
    config = make_app_config(
        schedules=[
            make_schedule(),
            make_schedule(label="Morning 2"),
        ],
    )
    with pytest.raises(ConfigValidationError):
        config.validate()


def test_archive_storage_root_is_required() -> None:
    config = make_app_config(archive_storage_root="")
    with pytest.raises(ConfigValidationError):
        config.validate()


def test_scheduler_sync_state_is_validated() -> None:
    config = make_app_config(scheduler_sync_state="broken")
    with pytest.raises(ConfigValidationError):
        config.validate()


def test_storage_preset_is_validated() -> None:
    config = make_app_config(storage_preset="dropbox")
    with pytest.raises(ConfigValidationError):
        config.validate()


def test_settings_window_size_floor_is_validated() -> None:
    config = make_app_config(
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


def test_app_config_from_dict_accepts_schema_4_and_preserves_extraction_fields() -> None:
    config = AppConfig.from_dict(
        {
            "schema_version": 4,
            "capture_storage_root": "C:\\captures",
            "archive_storage_root": "C:\\archive",
            "schedules": [
                {
                    "schedule_id": "night",
                    "label": "Night",
                    "interval_value": 1,
                    "interval_unit": "minute",
                    "start_date_local": "2026-03-25",
                    "start_time_local": "01:30:00",
                    "enabled": True,
                    "extraction_profile_id": "profile_night",
                }
            ],
            "extraction_profiles": [{"profile_id": "profile_night", "label": "Night profile"}],
        }
    )

    assert config.schema_version == 4
    assert config.schedules[0].extraction_profile_id == "profile_night"
    assert config.extraction_profiles == [{"profile_id": "profile_night", "label": "Night profile"}]


# ---------------------------------------------------------------------------
# AppConfig validation — uncovered branches
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"schema_version": 1}, "schema_version"),
        ({"capture_storage_root": ""}, "capture_storage_root"),
        ({"retention_mode": "delete_immediately"}, "retention_mode"),
        ({"retention_mode": "keep_days", "retention_days": None}, "retention_days"),
        ({"retention_mode": "keep_forever", "retention_days": 0}, "retention_days"),
        ({"log_level": "WARNING"}, "log_level"),
        ({"settings_window_height": SETTINGS_WINDOW_MIN_HEIGHT - 1}, "settings_window_height"),
        ({"slot_match_tolerance_seconds": -1}, "slot_match_tolerance_seconds"),
        ({"capture_mode": "screenshot"}, "capture_mode"),
        ({"image_format": "bmp"}, "image_format"),
        ({"image_quality": 0}, "image_quality"),
        ({"retention_grace_days": 0}, "retention_grace_days"),
        ({"extraction_profiles": [None]}, "extraction_profiles"),
    ],
)
def test_app_config_validation_rejects_invalid_values(
    overrides: dict[str, object],
    message: str,
) -> None:
    config = make_app_config(**overrides)

    with pytest.raises(ConfigValidationError, match=message):
        config.validate()


# ---------------------------------------------------------------------------
# AppConfig.mark_scheduler_sync_ok
# ---------------------------------------------------------------------------


def test_mark_scheduler_sync_ok_clears_failed_state() -> None:
    config = make_app_config()
    config.mark_scheduler_sync_failed("something broke")
    assert config.scheduler_sync_failed() is True

    config.mark_scheduler_sync_ok()
    assert config.scheduler_sync_failed() is False
    assert config.scheduler_sync_message is None


# ---------------------------------------------------------------------------
# AppConfig.get_schedule
# ---------------------------------------------------------------------------


def test_get_schedule_returns_none_for_unknown_id() -> None:
    config = make_app_config(schedules=[make_schedule(start_date_local="2026-01-01")])
    assert config.get_schedule("evening") is None


# ---------------------------------------------------------------------------
# Schedule validation — uncovered branches
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"interval_unit": "fortnight"}, "interval_unit"),
        ({"start_date_local": "not-a-date"}, "start_date_local"),
        ({"start_time_local": "99:00:00"}, "start_time_local"),
        ({"schedule_id": "HAS_UPPER"}, "schedule_id"),
        ({"label": "   "}, "label"),
        ({"interval_value": 0}, "interval_value"),
    ],
)
def test_schedule_validation_rejects_invalid_values(
    overrides: dict[str, object],
    message: str,
) -> None:
    sched = make_schedule(**overrides)

    with pytest.raises(ConfigValidationError, match=message):
        sched.validate()
