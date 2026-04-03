from __future__ import annotations

from selfsnap.models import CaptureMode, ConfigValidationError, ImageFormat, StoragePreset

_STORAGE_PRESET_LABELS = {
    StoragePreset.LOCAL_PICTURES.value: "Local Pictures",
    StoragePreset.ONEDRIVE_PICTURES.value: "OneDrive Pictures",
    StoragePreset.CUSTOM.value: "Custom Folder",
}

_RETENTION_MODE_LABELS = {
    "keep_forever": "Keep Forever",
    "keep_days": "Archive After N Days",
}

_SCHEDULER_SYNC_STATE_LABELS = {
    "ok": "Healthy",
    "failed": "Needs Attention",
}

_CAPTURE_MODE_LABELS = {
    CaptureMode.COMPOSITE.value: "Composite",
    CaptureMode.PER_MONITOR.value: "Per Monitor",
}

_IMAGE_FORMAT_LABELS = {
    ImageFormat.PNG.value: "PNG",
    ImageFormat.JPEG.value: "JPEG",
    ImageFormat.WEBP.value: "WEBP",
}


def local_privacy_notice() -> str:
    return (
        "SelfSnap stores captures locally, stays offline by default, and does not encrypt "
        "screenshots at rest in v1. Use only on a machine and storage location you control."
    )


def storage_preset_labels() -> list[str]:
    return list(_STORAGE_PRESET_LABELS.values())


def storage_preset_label(value: str) -> str:
    try:
        return _STORAGE_PRESET_LABELS[value]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported storage preset: {value}") from exc


def storage_preset_value(label: str) -> str:
    for value, display_label in _STORAGE_PRESET_LABELS.items():
        if label == display_label:
            return value
    raise ConfigValidationError(f"Unsupported storage preset label: {label}")


def retention_mode_labels() -> list[str]:
    return list(_RETENTION_MODE_LABELS.values())


def retention_mode_label(value: str) -> str:
    try:
        return _RETENTION_MODE_LABELS[value]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported retention mode: {value}") from exc


def retention_mode_value(label: str) -> str:
    for value, display_label in _RETENTION_MODE_LABELS.items():
        if label == display_label:
            return value
    raise ConfigValidationError(f"Unsupported retention mode label: {label}")


def scheduler_sync_state_label(value: str) -> str:
    try:
        return _SCHEDULER_SYNC_STATE_LABELS[value]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported scheduler sync state: {value}") from exc


def capture_mode_label(value: str) -> str:
    try:
        return _CAPTURE_MODE_LABELS[value]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported capture mode: {value}") from exc


def image_format_label(value: str) -> str:
    try:
        return _IMAGE_FORMAT_LABELS[value]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported image format: {value}") from exc


def notification_mode_label(
    notify_on_failed_or_missed: bool,
    notify_on_every_capture: bool,
) -> str:
    if notify_on_failed_or_missed and notify_on_every_capture:
        return "Failures, misses, and all successful captures"
    if notify_on_every_capture:
        return "All successful captures only"
    if notify_on_failed_or_missed:
        return "Failures and misses only"
    return "No tray notifications"


def retention_policy_label(
    retention_mode: str,
    retention_days: int | None,
    purge_enabled: bool,
    retention_grace_days: int,
) -> str:
    if retention_mode == "keep_forever":
        return "Keep forever"
    if retention_mode != "keep_days":
        raise ConfigValidationError(f"Unsupported retention mode: {retention_mode}")
    if retention_days is None or retention_days < 1:
        raise ConfigValidationError("retention_days must be >= 1 for keep_days mode")
    summary = f"Archive after {retention_days} {_day_label(retention_days)}"
    if purge_enabled:
        return (
            f"{summary}, purge {retention_grace_days} grace "
            f"{_day_label(retention_grace_days)} later"
        )
    return summary


def enabled_disabled_label(value: bool) -> str:
    return "Enabled" if value else "Disabled"


def on_off_label(value: bool) -> str:
    return "On" if value else "Off"


def yes_no_label(value: bool) -> str:
    return "Yes" if value else "No"


def _day_label(value: int) -> str:
    return "day" if value == 1 else "days"
