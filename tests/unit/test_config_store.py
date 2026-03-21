from __future__ import annotations

import json

import pytest

from selfsnap.config_store import load_or_create_config, load_config, save_config
from selfsnap.models import AppConfig, ConfigValidationError, Schedule


def test_load_or_create_creates_default(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    assert config.capture_storage_root == str(temp_paths.default_capture_root)
    assert temp_paths.config_path.exists()


def test_save_and_load_round_trip(temp_paths) -> None:
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        schedules=[Schedule(schedule_id="morning", label="Morning", local_time="09:00")],
    )
    save_config(temp_paths, config)
    loaded = load_config(temp_paths)
    assert loaded.schedules[0].schedule_id == "morning"


def test_invalid_config_file_raises(temp_paths) -> None:
    temp_paths.ensure_dirs()
    temp_paths.config_path.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
    with pytest.raises(ConfigValidationError):
        load_config(temp_paths)

