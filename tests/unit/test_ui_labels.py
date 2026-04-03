from __future__ import annotations

import pytest

from selfsnap.models import ConfigValidationError
from selfsnap.ui_labels import (
    capture_mode_label,
    capture_mode_value,
    local_privacy_notice,
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


def test_capture_mode_labels_round_trip() -> None:
    assert capture_mode_label("composite") == "Composite"
    assert capture_mode_label("per_monitor") == "Per Monitor"

    assert capture_mode_value("Composite") == "composite"
    assert capture_mode_value("Per Monitor") == "per_monitor"


def test_local_privacy_notice_matches_public_trust_boundary() -> None:
    notice = local_privacy_notice()

    assert "stores captures locally" in notice
    assert "offline by default" in notice
    assert "does not encrypt screenshots at rest in v1" in notice


def test_storage_preset_labels_returns_list() -> None:
    from selfsnap.ui_labels import storage_preset_labels
    labels = storage_preset_labels()
    assert "Local Pictures" in labels
    assert "OneDrive Pictures" in labels
    assert "Custom Folder" in labels


def test_retention_mode_labels_returns_list() -> None:
    from selfsnap.ui_labels import retention_mode_labels
    labels = retention_mode_labels()
    assert "Keep Forever" in labels
    assert "Archive After N Days" in labels


def test_storage_preset_label_invalid_raises() -> None:
    with pytest.raises(ConfigValidationError, match="Unsupported storage preset"):
        storage_preset_label("dropbox")


def test_storage_preset_value_invalid_raises() -> None:
    with pytest.raises(ConfigValidationError, match="Unsupported storage preset label"):
        storage_preset_value("Dropbox")


def test_retention_mode_label_invalid_raises() -> None:
    with pytest.raises(ConfigValidationError, match="Unsupported retention mode"):
        retention_mode_label("delete_all")


def test_retention_mode_value_invalid_raises() -> None:
    with pytest.raises(ConfigValidationError, match="Unsupported retention mode label"):
        retention_mode_value("Delete All")


def test_capture_mode_label_invalid_raises() -> None:
    with pytest.raises(ConfigValidationError, match="Unsupported capture mode"):
        capture_mode_label("windowed")


def test_capture_mode_value_invalid_raises() -> None:
    with pytest.raises(ConfigValidationError, match="Unsupported capture mode label"):
        capture_mode_value("Windowed")
