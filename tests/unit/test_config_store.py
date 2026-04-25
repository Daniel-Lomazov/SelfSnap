from __future__ import annotations

import json

import pytest

from selfsnap.config_store import load_config, load_or_create_config, save_config
from selfsnap.models import ConfigValidationError
from selfsnap.window_sizing import DEFAULT_SETTINGS_WINDOW_HEIGHT, DEFAULT_SETTINGS_WINDOW_WIDTH
from tests.support.factories import make_app_config, make_schedule


def test_load_or_create_creates_default(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    assert config.app_enabled is False
    assert config.first_run_completed is False
    assert config.storage_preset == "local_pictures"
    assert config.capture_storage_root == str(temp_paths.default_capture_root)
    assert config.archive_storage_root == str(temp_paths.default_archive_root)
    assert config.settings_window_width == DEFAULT_SETTINGS_WINDOW_WIDTH
    assert config.settings_window_height == DEFAULT_SETTINGS_WINDOW_HEIGHT
    assert config.scheduler_sync_state == "ok"
    assert temp_paths.config_path.exists()


def test_save_and_load_round_trip(temp_paths) -> None:
    config = make_app_config(
        temp_paths=temp_paths,
        settings_window_width=1000,
        settings_window_height=800,
        schedules=[make_schedule()],
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

    assert loaded.schema_version == 4
    assert loaded.schedules[0].interval_value == 1
    assert loaded.schedules[0].interval_unit == "day"
    assert loaded.schedules[0].start_time_local == "08:15:00"


def test_load_and_save_preserves_schema_4_extraction_fields(temp_paths) -> None:
    temp_paths.ensure_dirs()
    payload = {
        "schema_version": 4,
        "app_enabled": False,
        "first_run_completed": True,
        "storage_preset": "local_pictures",
        "capture_storage_root": str(temp_paths.default_capture_root),
        "archive_storage_root": str(temp_paths.default_archive_root),
        "settings_window_width": 960,
        "settings_window_height": 760,
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
    temp_paths.config_path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_config(temp_paths)

    assert loaded.schema_version == 4
    assert loaded.schedules[0].extraction_profile_id == "profile_night"
    assert loaded.extraction_profiles == payload["extraction_profiles"]

    save_config(temp_paths, loaded)
    persisted = json.loads(temp_paths.config_path.read_text(encoding="utf-8"))
    assert persisted["schema_version"] == 4
    assert persisted["schedules"][0]["extraction_profile_id"] == "profile_night"
    assert persisted["extraction_profiles"] == payload["extraction_profiles"]


# ---------------------------------------------------------------------------
# validate_config_file — error paths
# ---------------------------------------------------------------------------


def test_validate_config_file_raises_on_corrupt_json(temp_paths) -> None:
    from selfsnap.config_store import validate_config_file

    temp_paths.ensure_dirs()
    temp_paths.config_path.write_text("{ not valid json }", encoding="utf-8")
    with pytest.raises(ConfigValidationError):
        validate_config_file(temp_paths)


def test_validate_config_file_raises_on_invalid_schema(temp_paths) -> None:
    import json

    from selfsnap.config_store import validate_config_file

    temp_paths.ensure_dirs()
    temp_paths.config_path.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
    with pytest.raises(ConfigValidationError):
        validate_config_file(temp_paths)


# ---------------------------------------------------------------------------
# load_or_create_config — when config already exists
# ---------------------------------------------------------------------------


def test_load_or_create_returns_existing_config(temp_paths) -> None:
    from selfsnap.config_store import load_or_create_config, save_config

    first = load_or_create_config(temp_paths)
    first.settings_window_width = 1234
    save_config(temp_paths, first)

    second = load_or_create_config(temp_paths)
    assert second.settings_window_width == 1234


def test_load_config_clamps_legacy_settings_window_geometry(temp_paths) -> None:
    temp_paths.ensure_dirs()
    temp_paths.config_path.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "app_enabled": False,
                "first_run_completed": True,
                "storage_preset": "local_pictures",
                "capture_storage_root": str(temp_paths.default_capture_root),
                "archive_storage_root": str(temp_paths.default_archive_root),
                "settings_window_width": 420,
                "settings_window_height": 520,
                "schedules": [],
            }
        ),
        encoding="utf-8",
    )

    loaded = load_config(temp_paths)

    assert loaded.settings_window_width == 960
    assert loaded.settings_window_height == 760


# ---------------------------------------------------------------------------
# save_config — atomic write (temp file is cleaned up)
# ---------------------------------------------------------------------------


def test_save_config_does_not_leave_temp_files(temp_paths) -> None:
    from selfsnap.config_store import load_or_create_config, save_config

    config = load_or_create_config(temp_paths)
    save_config(temp_paths, config)
    temp_files = list(temp_paths.config_path.parent.glob("*.tmp"))
    assert temp_files == []


def test_load_config_returns_default_when_file_missing(temp_paths) -> None:
    """config_store.py line 25: load_config returns default when file doesn't exist."""
    temp_paths.ensure_dirs()
    assert not temp_paths.config_path.exists()

    config = load_config(temp_paths)

    assert config.app_enabled is False
    assert config.first_run_completed is False

