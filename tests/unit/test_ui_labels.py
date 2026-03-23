from __future__ import annotations

from selfsnap.ui_labels import (
    retention_mode_label,
    retention_mode_value,
    storage_preset_label,
    storage_preset_value,
)


def test_storage_preset_labels_round_trip() -> None:
    assert storage_preset_label("local_pictures") == "Local Pictures"
    assert storage_preset_label("onedrive_pictures") == "OneDrive Pictures"
    assert storage_preset_label("custom") == "Custom Folder"

    assert storage_preset_value("Local Pictures") == "local_pictures"
    assert storage_preset_value("OneDrive Pictures") == "onedrive_pictures"
    assert storage_preset_value("Custom Folder") == "custom"


def test_retention_mode_labels_round_trip() -> None:
    assert retention_mode_label("keep_forever") == "Keep Forever"
    assert retention_mode_label("keep_days") == "Archive After N Days"

    assert retention_mode_value("Keep Forever") == "keep_forever"
    assert retention_mode_value("Archive After N Days") == "keep_days"
