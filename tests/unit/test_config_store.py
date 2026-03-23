from __future__ import annotations

import json

import pytest

from selfsnap.config_store import load_or_create_config, load_config, save_config
from selfsnap.models import AppConfig, ConfigValidationError, Schedule


def test_load_or_create_creates_default(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    assert config.app_enabled is False
    assert config.first_run_completed is False
    assert config.storage_preset == "local_pictures"
    assert config.capture_storage_root == str(temp_paths.default_capture_root)
    assert config.archive_storage_root == str(temp_paths.default_archive_root)
    assert config.settings_window_width == 960
    assert config.settings_window_height == 760
    assert config.scheduler_sync_state == "ok"
    assert temp_paths.config_path.exists()


def test_save_and_load_round_trip(temp_paths) -> None:
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
        settings_window_width=1000,
        settings_window_height=800,
        schedules=[
            Schedule(
                schedule_id="morning",
                label="Morning",
                interval_value=1,
                interval_unit="day",
                start_date_local="2026-03-23",
                start_time_local="09:00:00",
            )
        ],
    )
    save_config(temp_paths, config)
    loaded = load_config(temp_paths)
    assert loaded.schedules[0].schedule_id == "morning"
    assert loaded.settings_window_width == 1000
    assert loaded.settings_window_height == 800


def test_invalid_config_file_raises(temp_paths) -> None:
    temp_paths.ensure_dirs()
    temp_paths.config_path.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
    with pytest.raises(ConfigValidationError):
        load_config(temp_paths)


def test_load_config_migrates_legacy_schedule_shape(temp_paths) -> None:
    temp_paths.ensure_dirs()
    temp_paths.config_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "app_enabled": False,
                "capture_storage_root": str(temp_paths.default_capture_root),
                "archive_storage_root": str(temp_paths.default_archive_root),
                "schedules": [
                    {
                        "schedule_id": "legacy",
                        "label": "Legacy",
                        "local_time": "08:15",
                        "enabled": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    loaded = load_config(temp_paths)

    assert loaded.schema_version == 2
    assert loaded.schedules[0].interval_value == 1
    assert loaded.schedules[0].interval_unit == "day"
    assert loaded.schedules[0].start_time_local == "08:15:00"
