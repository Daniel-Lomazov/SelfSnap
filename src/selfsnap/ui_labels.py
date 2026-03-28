from __future__ import annotations

from selfsnap.models import ConfigValidationError, StoragePreset

_STORAGE_PRESET_LABELS = {
    StoragePreset.LOCAL_PICTURES.value: "Local Pictures",
    StoragePreset.ONEDRIVE_PICTURES.value: "OneDrive Pictures",
    StoragePreset.CUSTOM.value: "Custom Folder",
}

_RETENTION_MODE_LABELS = {
    "keep_forever": "Keep Forever",
    "keep_days": "Archive After N Days",
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
