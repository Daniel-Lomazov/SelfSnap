from __future__ import annotations

import pytest

from selfsnap.models import ConfigValidationError
from selfsnap.ui_labels import (
    capture_mode_label,
    enabled_disabled_label,
    image_format_label,
    local_privacy_notice,
    notification_mode_label,
    on_off_label,
    retention_mode_label,
    retention_mode_value,
    retention_policy_label,
    scheduler_sync_state_label,
    storage_preset_label,
    storage_preset_value,
    yes_no_label,
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


def test_status_and_format_labels_cover_diagnostics_views() -> None:
    assert scheduler_sync_state_label("ok") == "Healthy"
    assert scheduler_sync_state_label("failed") == "Needs Attention"
    assert capture_mode_label("composite") == "Composite"
    assert capture_mode_label("per_monitor") == "Per Monitor"
    assert image_format_label("png") == "PNG"
    assert image_format_label("jpeg") == "JPEG"
    assert image_format_label("webp") == "WEBP"


def test_notification_retention_and_boolean_labels_are_human_readable() -> None:
    assert notification_mode_label(True, False) == "Failures and misses only"
    assert notification_mode_label(True, True) == "Failures, misses, and all successful captures"
    assert notification_mode_label(False, True) == "All successful captures only"
    assert notification_mode_label(False, False) == "No tray notifications"
    assert retention_policy_label("keep_forever", None, False, 30) == "Keep forever"
    assert retention_policy_label("keep_days", 14, False, 30) == "Archive after 14 days"
    assert (
        retention_policy_label("keep_days", 14, True, 7)
        == "Archive after 14 days, purge 7 grace days later"
    )
    assert enabled_disabled_label(True) == "Enabled"
    assert enabled_disabled_label(False) == "Disabled"
    assert on_off_label(True) == "On"
    assert on_off_label(False) == "Off"
    assert yes_no_label(True) == "Yes"
    assert yes_no_label(False) == "No"


def test_scheduler_sync_state_and_retention_policy_invalid_values_raise() -> None:
    with pytest.raises(ConfigValidationError, match="Unsupported scheduler sync state"):
        scheduler_sync_state_label("stale")

    with pytest.raises(ConfigValidationError, match="retention_days must be >= 1"):
        retention_policy_label("keep_days", 0, False, 30)
