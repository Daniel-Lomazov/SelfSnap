from __future__ import annotations

import pytest

from selfsnap.config_store import load_config, save_config
from selfsnap.models import AppConfig, ConfigValidationError, StoragePreset
from selfsnap.storage import apply_storage_preset, infer_storage_preset, preset_roots


def test_save_config_normalizes_local_storage_preset(temp_paths) -> None:
    config = AppConfig(
        storage_preset=StoragePreset.LOCAL_PICTURES.value,
        capture_storage_root="C:\\elsewhere",
        archive_storage_root="C:\\elsewhere-archive",
    )

    save_config(temp_paths, config)
    loaded = load_config(temp_paths)

    assert loaded.capture_storage_root == str(temp_paths.default_capture_root)
    assert loaded.archive_storage_root == str(temp_paths.default_archive_root)


def test_apply_storage_preset_uses_onedrive_when_available(temp_paths, monkeypatch) -> None:
    onedrive_root = temp_paths.user_profile / "OneDrive"
    onedrive_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("OneDrive", str(onedrive_root))
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
    )

    updated = apply_storage_preset(temp_paths, config, StoragePreset.ONEDRIVE_PICTURES.value)

    assert updated.capture_storage_root == str(onedrive_root / "Pictures" / "SelfSnap" / "captures")
    assert updated.archive_storage_root == str(onedrive_root / "Pictures" / "SelfSnap" / "archive")


def test_save_config_blocks_missing_onedrive_root(temp_paths, monkeypatch) -> None:
    monkeypatch.delenv("OneDrive", raising=False)
    config = AppConfig(
        storage_preset=StoragePreset.ONEDRIVE_PICTURES.value,
        capture_storage_root=str(temp_paths.onedrive_capture_root()),
        archive_storage_root=str(temp_paths.onedrive_archive_root()),
    )

    with pytest.raises(ConfigValidationError):
        save_config(temp_paths, config)


def test_preset_roots_raises_for_unknown_preset(temp_paths) -> None:
    with pytest.raises(ConfigValidationError, match="Unsupported storage preset"):
        preset_roots(temp_paths, "dropbox")


def test_infer_storage_preset_returns_custom_for_unknown_roots(temp_paths) -> None:
    result = infer_storage_preset(temp_paths, "C:\\custom_cap", "C:\\custom_arc")
    assert result == StoragePreset.CUSTOM.value


def test_infer_storage_preset_detects_onedrive(temp_paths, monkeypatch) -> None:
    onedrive_root = temp_paths.user_profile / "OneDrive"
    onedrive_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("OneDrive", str(onedrive_root))
    cap = str(temp_paths.onedrive_capture_root())
    arc = str(temp_paths.onedrive_archive_root())
    result = infer_storage_preset(temp_paths, cap, arc)
    assert result == StoragePreset.ONEDRIVE_PICTURES.value


def test_infer_storage_preset_detects_local_pictures(temp_paths) -> None:
    cap = str(temp_paths.default_capture_root)
    arc = str(temp_paths.default_archive_root)
    result = infer_storage_preset(temp_paths, cap, arc)
    assert result == StoragePreset.LOCAL_PICTURES.value


def test_save_config_blocks_unwritable_onedrive_root2(temp_paths, monkeypatch) -> None:
    onedrive_root = temp_paths.user_profile / "OneDrive"
    onedrive_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("OneDrive", str(onedrive_root))
    monkeypatch.setattr("selfsnap.storage.os.access", lambda _path, _mode: False)
    config = AppConfig(
        storage_preset=StoragePreset.ONEDRIVE_PICTURES.value,
        capture_storage_root=str(temp_paths.onedrive_capture_root()),
        archive_storage_root=str(temp_paths.onedrive_archive_root()),
    )

    with pytest.raises(ConfigValidationError):
        save_config(temp_paths, config)
