from __future__ import annotations

from selfsnap.models import ConfigValidationError, StoragePreset

_STORAGE_PRESET_LABELS = {
    StoragePreset.LOCAL_PICTURES.value: "Local Pictures",
    StoragePreset.ONEDRIVE_PICTURES.value: "OneDrive Pictures",
    StoragePreset.CUSTOM.value: "Custom Folder",
}
_STORAGE_PRESET_LABEL_TO_VALUE = {label: value for value, label in _STORAGE_PRESET_LABELS.items()}

_RETENTION_MODE_LABELS = {
    "keep_forever": "Keep Forever",
    "keep_days": "Archive After N Days",
}
_RETENTION_MODE_LABEL_TO_VALUE = {label: value for value, label in _RETENTION_MODE_LABELS.items()}

_CAPTURE_MODE_LABELS = {
    "composite": "Composite",
    "per_monitor": "Per Monitor",
}
_CAPTURE_MODE_LABEL_TO_VALUE = {label: value for value, label in _CAPTURE_MODE_LABELS.items()}

_IMAGE_FORMAT_LABELS = {
    "png": "PNG",
    "jpeg": "JPEG",
    "webp": "WEBP",
}
_IMAGE_FORMAT_LABEL_TO_VALUE = {label: value for value, label in _IMAGE_FORMAT_LABELS.items()}


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
    try:
        return _STORAGE_PRESET_LABEL_TO_VALUE[label]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported storage preset label: {label}") from exc


def retention_mode_labels() -> list[str]:
    return list(_RETENTION_MODE_LABELS.values())


def retention_mode_label(value: str) -> str:
    try:
        return _RETENTION_MODE_LABELS[value]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported retention mode: {value}") from exc


def retention_mode_value(label: str) -> str:
    try:
        return _RETENTION_MODE_LABEL_TO_VALUE[label]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported retention mode label: {label}") from exc


def capture_mode_labels() -> list[str]:
    return list(_CAPTURE_MODE_LABELS.values())


def capture_mode_label(value: str) -> str:
    try:
        return _CAPTURE_MODE_LABELS[value]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported capture mode: {value}") from exc


def capture_mode_value(label: str) -> str:
    try:
        return _CAPTURE_MODE_LABEL_TO_VALUE[label]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported capture mode label: {label}") from exc


def image_format_labels() -> list[str]:
    return list(_IMAGE_FORMAT_LABELS.values())


def image_format_label(value: str) -> str:
    try:
        return _IMAGE_FORMAT_LABELS[value]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported image format: {value}") from exc


def image_format_value(label: str) -> str:
    try:
        return _IMAGE_FORMAT_LABEL_TO_VALUE[label]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported image format label: {label}") from exc
