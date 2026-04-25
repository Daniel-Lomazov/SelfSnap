from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from selfsnap.models import AppConfig, Schedule
from selfsnap.paths import AppPaths


DEFAULT_CAPTURE_ROOT = "C:\\captures"
DEFAULT_ARCHIVE_ROOT = "C:\\archive"


def make_schedule(**overrides: Any) -> Schedule:
    payload: dict[str, Any] = {
        "schedule_id": "morning",
        "label": "Morning",
        "interval_value": 1,
        "interval_unit": "day",
        "start_date_local": "2026-03-23",
        "start_time_local": "09:00:00",
        "enabled": True,
        "extraction_profile_id": None,
    }
    payload.update(overrides)
    return Schedule(**payload)


def make_app_config(
    *,
    temp_paths: AppPaths | None = None,
    schedules: Sequence[Schedule] | None = None,
    extraction_profiles: Sequence[dict[str, Any]] | None = None,
    **overrides: Any,
) -> AppConfig:
    payload: dict[str, Any] = {
        "capture_storage_root": (
            str(temp_paths.default_capture_root) if temp_paths else DEFAULT_CAPTURE_ROOT
        ),
        "archive_storage_root": (
            str(temp_paths.default_archive_root) if temp_paths else DEFAULT_ARCHIVE_ROOT
        ),
        "schedules": list(schedules) if schedules is not None else [],
        "extraction_profiles": list(extraction_profiles) if extraction_profiles is not None else [],
    }
    payload.update(overrides)
    return AppConfig(**payload)
