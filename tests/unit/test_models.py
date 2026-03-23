from __future__ import annotations

import pytest

from selfsnap.models import AppConfig, ConfigValidationError, Schedule


def test_duplicate_schedule_ids_are_rejected() -> None:
    config = AppConfig(
        capture_storage_root="C:\\captures",
        archive_storage_root="C:\\archive",
        schedules=[
            Schedule(schedule_id="morning", label="Morning", local_time="09:00"),
            Schedule(schedule_id="morning", label="Morning 2", local_time="10:00"),
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
        settings_window_width=900,
        settings_window_height=700,
    )
    with pytest.raises(ConfigValidationError):
        config.validate()
