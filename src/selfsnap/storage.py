from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

from selfsnap.models import AppConfig, ConfigValidationError, StoragePreset
from selfsnap.paths import AppPaths


def preset_roots(paths: AppPaths, preset: str) -> tuple[Path, Path]:
    if preset == StoragePreset.LOCAL_PICTURES.value:
        return paths.default_capture_root, paths.default_archive_root
    if preset == StoragePreset.ONEDRIVE_PICTURES.value:
        return paths.onedrive_capture_root(), paths.onedrive_archive_root()
    raise ConfigValidationError(f"Unsupported storage preset: {preset}")


def apply_storage_preset(
    paths: AppPaths, config: AppConfig, preset: str, validate: bool = True
) -> AppConfig:
    capture_root, archive_root = preset_roots(paths, preset)
    updated = replace(
        config,
        storage_preset=preset,
        capture_storage_root=str(capture_root),
        archive_storage_root=str(archive_root),
    )
    if validate:
        validate_storage_config(paths, updated)
    return updated


def normalize_storage_config(
    paths: AppPaths, config: AppConfig, validate: bool = True
) -> AppConfig:
    if config.storage_preset == StoragePreset.CUSTOM.value:
        if validate:
            validate_storage_config(paths, config)
        return config
    return apply_storage_preset(paths, config, config.storage_preset, validate=validate)


def infer_storage_preset(paths: AppPaths, capture_root: str, archive_root: str) -> str:
    normalized_capture = Path(capture_root).expanduser()
    normalized_archive = Path(archive_root).expanduser()
    local_capture, local_archive = preset_roots(paths, StoragePreset.LOCAL_PICTURES.value)
    onedrive_capture, onedrive_archive = preset_roots(paths, StoragePreset.ONEDRIVE_PICTURES.value)
    if normalized_capture == local_capture and normalized_archive == local_archive:
        return StoragePreset.LOCAL_PICTURES.value
    if normalized_capture == onedrive_capture and normalized_archive == onedrive_archive:
        return StoragePreset.ONEDRIVE_PICTURES.value
    return StoragePreset.CUSTOM.value


def validate_storage_config(paths: AppPaths, config: AppConfig) -> None:
    if config.storage_preset == StoragePreset.ONEDRIVE_PICTURES.value:
        onedrive_root = paths.preferred_onedrive_root()
        if not onedrive_root.exists() or not onedrive_root.is_dir():
            raise ConfigValidationError(
                f"OneDrive storage preset requires an existing OneDrive root at {onedrive_root}"
            )
        _validate_writable_target(paths.resolve_capture_root(config))
        _validate_writable_target(paths.resolve_archive_root(config))


def _validate_writable_target(target: Path) -> None:
    existing_parent = _nearest_existing_parent(target)
    if existing_parent is None:
        raise ConfigValidationError(f"Storage target is not reachable: {target}")
    if not os.access(existing_parent, os.W_OK):
        raise ConfigValidationError(f"Storage target is not writable: {existing_parent}")


def _nearest_existing_parent(target: Path) -> Path | None:
    current = target
    while True:
        if current.exists():
            return current if current.is_dir() else current.parent
        if current.parent == current:
            return None
        current = current.parent
