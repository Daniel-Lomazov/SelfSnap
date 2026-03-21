from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from selfsnap.models import AppConfig, ConfigValidationError
from selfsnap.paths import AppPaths


def default_config(paths: AppPaths) -> AppConfig:
    config = AppConfig(
        app_enabled=False,
        first_run_completed=False,
        capture_storage_root=str(paths.default_capture_root),
        archive_storage_root=str(paths.default_archive_root),
    )
    config.validate()
    return config


def load_config(paths: AppPaths) -> AppConfig:
    if not paths.config_path.exists():
        return default_config(paths)
    with paths.config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not data.get("capture_storage_root"):
        data["capture_storage_root"] = str(paths.default_capture_root)
    if not data.get("archive_storage_root"):
        data["archive_storage_root"] = str(paths.default_archive_root)
    return AppConfig.from_dict(data)


def load_or_create_config(paths: AppPaths) -> AppConfig:
    paths.ensure_dirs()
    if not paths.config_path.exists():
        config = default_config(paths)
        save_config(paths, config)
        return config
    return load_config(paths)


def save_config(paths: AppPaths, config: AppConfig) -> None:
    config.validate()
    paths.ensure_dirs()
    payload = json.dumps(config.to_dict(), indent=2)
    temp_parent = paths.config_path.parent
    temp_parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", delete=False, dir=temp_parent, encoding="utf-8") as temp_file:
        temp_file.write(payload)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_path = Path(temp_file.name)
    temp_path.replace(paths.config_path)


def validate_config_file(paths: AppPaths) -> None:
    try:
        load_config(paths)
    except (json.JSONDecodeError, ConfigValidationError) as exc:
        raise ConfigValidationError(str(exc)) from exc
