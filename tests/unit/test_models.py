from __future__ import annotations

import pytest

from selfsnap.models import AppConfig, ConfigValidationError, Schedule


def test_duplicate_schedule_ids_are_rejected() -> None:
    config = AppConfig(
        capture_storage_root="C:\\captures",
        schedules=[
            Schedule(schedule_id="morning", label="Morning", local_time="09:00"),
            Schedule(schedule_id="morning", label="Morning 2", local_time="10:00"),
        ],
    )
    with pytest.raises(ConfigValidationError):
        config.validate()


def test_pause_until_is_validated() -> None:
    config = AppConfig(capture_storage_root="C:\\captures", pause_until_local="not-a-date")
    with pytest.raises(ConfigValidationError):
        config.validate()

