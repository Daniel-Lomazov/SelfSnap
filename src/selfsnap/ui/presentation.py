from __future__ import annotations

from selfsnap.models import AppConfig
from selfsnap.ui_labels import capture_mode_label, retention_mode_label, storage_preset_label


def settings_header_status(config: AppConfig) -> tuple[str, str]:
    if config.scheduler_sync_failed():
        return "Scheduler sync needs attention", "warning"
    if not config.first_run_completed:
        return "Setup in progress", "info"
    if config.app_enabled:
        return "Scheduled capture enabled", "accent"
    return "Manual capture only", "neutral"


def scheduler_status_detail(config: AppConfig) -> str | None:
    if not config.scheduler_sync_failed():
        return None
    if config.scheduler_sync_message:
        return f"Task Scheduler last reported an issue: {config.scheduler_sync_message}"
    return "Task Scheduler last reported an issue. Saving settings will retry the sync."


def storage_summary_text(
    *,
    storage_preset: str,
    retention_mode: str,
    retention_days: int | str | None,
    capture_mode: str,
    image_format: str,
    image_quality: int | str | None,
    purge_enabled: bool,
    retention_grace_days: int | str | None,
) -> str:
    parts = [
        _safe_storage_label(storage_preset),
        _retention_summary(retention_mode, retention_days),
        _capture_summary(capture_mode, image_format, image_quality),
    ]
    if purge_enabled:
        grace_days = _safe_positive_int_text(retention_grace_days, fallback="?")
        parts.append(f"Purges after {grace_days}-day grace")
    return " • ".join(part for part in parts if part)


def visibility_summary_text(
    *,
    start_tray_on_login: bool,
    wake_for_scheduled_captures: bool,
    show_last_capture_status: bool,
    notify_on_failed_or_missed: bool,
    notify_on_every_capture: bool,
    show_capture_overlay: bool,
) -> str:
    notification_text = "Notifications off"
    if notify_on_every_capture:
        notification_text = "All capture notifications"
    elif notify_on_failed_or_missed:
        notification_text = "Failure notifications"

    parts = [
        "Launches on sign-in" if start_tray_on_login else "Manual tray launch",
        "Wake requests on" if wake_for_scheduled_captures else "Wake requests off",
        "Tray status visible" if show_last_capture_status else "Tray status hidden",
        notification_text,
        "Overlay on" if show_capture_overlay else "Overlay off",
    ]
    return " • ".join(parts)


def maintenance_summary_text() -> str:
    return "Reset capture history, schedules, logs, and local settings from one place."


def tray_state_label(config: AppConfig) -> str:
    if not config.first_run_completed:
        return "Setup required"
    if not config.app_enabled:
        return "Scheduled captures paused"
    return "Scheduled captures on"


def tray_warning_label(config: AppConfig) -> str | None:
    if not config.scheduler_sync_failed():
        return None
    return "Scheduler needs attention - open Settings"


def tray_icon_title(config: AppConfig) -> str:
    if config.scheduler_sync_failed():
        return "SelfSnap Win11 - scheduler sync failed"
    if not config.first_run_completed:
        return "SelfSnap Win11 - setup required"
    return "SelfSnap Win11"


def tray_toggle_enabled_label(app_enabled: bool) -> str:
    return "Pause Scheduled Captures" if app_enabled else "Resume Scheduled Captures"


def latest_capture_label(outcome_code: str, timestamp_local: str) -> str:
    return f"Last capture: {_humanize_outcome_code(outcome_code)} at {timestamp_local}"


def tray_status_summary_label(state_text: str, latest_text: str | None = None) -> str:
    if latest_text:
        return f"{state_text} • {latest_text}"
    return state_text


def record_message(outcome_code: str, schedule_id: str | None) -> str:
    schedule_suffix = f" ({schedule_id})" if schedule_id else ""
    return f"{outcome_code}{schedule_suffix}"


def _safe_storage_label(value: str) -> str:
    try:
        return storage_preset_label(value)
    except Exception:
        return value


def _humanize_outcome_code(value: str) -> str:
    if value == "capture_saved":
        return "Saved"
    return value.replace("_", " ").capitalize()


def _retention_summary(value: str, days: int | str | None) -> str:
    if value == "keep_days":
        return f"Archives after {_safe_positive_int_text(days, fallback='N')} days"
    try:
        label = retention_mode_label(value)
    except Exception:
        return value
    if label == "Keep Forever":
        return "Keeps every capture"
    return label


def _capture_summary(
    capture_mode: str,
    image_format: str,
    image_quality: int | str | None,
) -> str:
    try:
        mode_label = capture_mode_label(capture_mode)
    except Exception:
        mode_label = capture_mode
    summary = f"{mode_label} {image_format.upper()}"
    if image_format.lower() in {"jpeg", "webp"}:
        summary = f"{summary} {_safe_positive_int_text(image_quality, fallback='?')}%"
    return summary


def _safe_positive_int_text(value: int | str | None, *, fallback: str) -> str:
    if isinstance(value, int):
        return str(value) if value > 0 else fallback
    if value is None:
        return fallback
    text = str(value).strip()
    if text.isdigit() and int(text) > 0:
        return text
    return fallback
