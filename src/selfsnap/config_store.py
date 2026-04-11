from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from selfsnap.models import AppConfig, ConfigValidationError
from selfsnap.paths import AppPaths
from selfsnap.storage import infer_storage_preset, normalize_storage_config


_MIN_SETTINGS_WINDOW_WIDTH = 960
_MIN_SETTINGS_WINDOW_HEIGHT = 760


def default_config(paths: AppPaths) -> AppConfig:
    config = AppConfig(
        app_enabled=False,
        first_run_completed=False,
        capture_storage_root=str(paths.default_capture_root),
        archive_storage_root=str(paths.default_archive_root),
    )
    return normalize_storage_config(paths, config)


def load_config(paths: AppPaths) -> AppConfig:
    if not paths.config_path.exists():
        return default_config(paths)
    with paths.config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not data.get("storage_preset"):
        data["storage_preset"] = infer_storage_preset(
            paths,
            str(data.get("capture_storage_root", "")),
            str(data.get("archive_storage_root", "")),
        )
    if not data.get("capture_storage_root"):
        data["capture_storage_root"] = str(paths.default_capture_root)
    if not data.get("archive_storage_root"):
        data["archive_storage_root"] = str(paths.default_archive_root)
    # Backward-compatible migration for older saved geometry values that predate
    # current minimum window constraints.
    try:
        data["settings_window_width"] = max(
            int(data.get("settings_window_width", _MIN_SETTINGS_WINDOW_WIDTH)),
            _MIN_SETTINGS_WINDOW_WIDTH,
        )
        data["settings_window_height"] = max(
            int(data.get("settings_window_height", _MIN_SETTINGS_WINDOW_HEIGHT)),
            _MIN_SETTINGS_WINDOW_HEIGHT,
        )
    except (TypeError, ValueError):
        data["settings_window_width"] = _MIN_SETTINGS_WINDOW_WIDTH
        data["settings_window_height"] = _MIN_SETTINGS_WINDOW_HEIGHT
    return normalize_storage_config(paths, AppConfig.from_dict(data), validate=False)


def load_or_create_config(paths: AppPaths) -> AppConfig:
    paths.ensure_dirs()
    if not paths.config_path.exists():
        config = default_config(paths)
        save_config(paths, config)
        return config
    return load_config(paths)


def save_config(paths: AppPaths, config: AppConfig) -> None:
    config = normalize_storage_config(paths, config)
    config.validate()
    paths.ensure_dirs()
    payload = json.dumps(config.to_dict(), indent=2)
    temp_parent = paths.config_path.parent
    temp_parent.mkdir(parents=True, exist_ok=True)
    temp_path = temp_parent / f"{paths.config_path.name}.{uuid4().hex}.tmp"
    with temp_path.open("w", encoding="utf-8") as temp_file:
        temp_file.write(payload)
        temp_file.flush()
        os.fsync(temp_file.fileno())
    temp_path.replace(paths.config_path)


def validate_config_file(paths: AppPaths) -> None:
    try:
        load_config(paths)
    except (json.JSONDecodeError, ConfigValidationError) as exc:
        raise ConfigValidationError(str(exc)) from exc
