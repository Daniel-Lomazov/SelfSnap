from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from selfsnap.models import AppConfig, CaptureRecord
from selfsnap.tray.schedule_editor import RecurringScheduleDraft, schedule_collection_summary
from selfsnap.ui_labels import retention_mode_label, storage_preset_label


@dataclass(slots=True, frozen=True)
class SettingsHeroState:
    headline: str
    message: str
    details: tuple[str, ...]


def format_local_timestamp(utc_text: str, *, empty_text: str = "(unknown time)") -> str:
    if not utc_text:
        return empty_text
    text = utc_text.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return utc_text[:19].replace("T", " ")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def format_latest_record_label(record: CaptureRecord | None) -> str:
    if record is None:
        return "Latest capture: none yet"
    timestamp_utc = record.started_utc or record.created_utc or ""
    return f"Latest capture: {record.outcome_code} at {format_local_timestamp(timestamp_utc)}"


def tray_state_label(config: AppConfig) -> str:
    if not config.first_run_completed:
        return "Status: setup required"
    if not config.app_enabled:
        return "Status: paused"
    if config.scheduler_sync_failed():
        return "Status: running, scheduler needs attention"
    return "Status: running"


def tray_scheduler_warning_label(config: AppConfig) -> str | None:
    if not config.scheduler_sync_failed():
        return None
    return "Scheduler sync failed. Open Settings."


def tray_toggle_label(config: AppConfig) -> str:
    return "Pause Scheduled Captures" if config.app_enabled else "Enable Scheduled Captures"


def tray_icon_title(config: AppConfig) -> str:
    if config.scheduler_sync_failed():
        return "SelfSnap Win11 - scheduler needs attention"
    if not config.first_run_completed:
        return "SelfSnap Win11 - setup required"
    if not config.app_enabled:
        return "SelfSnap Win11 - paused"
    return "SelfSnap Win11"


def disclosure_button_label(title: str, expanded: bool) -> str:
    return f"{'Hide' if expanded else 'Show'} {title.lower()}"


def settings_hero_state(
    config: AppConfig,
    drafts: Sequence[RecurringScheduleDraft],
    latest_label: str,
) -> SettingsHeroState:
    if not config.first_run_completed:
        headline = "Finish setup"
        message = "SelfSnap stays paused until first-run setup is complete."
    elif not config.app_enabled:
        headline = "Paused"
        message = "Scheduled captures are off. Capture now still works."
    elif config.scheduler_sync_failed():
        headline = "Needs attention"
        message = "Quick captures still work, but Windows scheduler sync should be reviewed."
    else:
        headline = "Ready"
        message = "SelfSnap is configured for calm, background capture."

    details = (
        latest_label,
        f"Schedules: {schedule_collection_summary(drafts)}",
        f"Storage: {storage_preset_label(config.storage_preset)}",
    )
    if config.scheduler_sync_failed() and config.scheduler_sync_message:
        details = (*details, f"Scheduler: {config.scheduler_sync_message}")
    return SettingsHeroState(headline=headline, message=message, details=details)


def storage_section_summary(config: AppConfig) -> str:
    retention = retention_mode_label(config.retention_mode)
    if config.retention_mode == "keep_days" and config.retention_days is not None:
        retention = f"{retention} ({config.retention_days} days)"
    return f"{storage_preset_label(config.storage_preset)} • {retention}"


def notifications_section_summary(config: AppConfig) -> str:
    startup = "Starts with Windows" if config.start_tray_on_login else "Starts manually"
    if config.notify_on_every_capture:
        notifications = "Alerts on every capture"
    elif config.notify_on_failed_or_missed:
        notifications = "Alerts on failed or missed captures"
    else:
        notifications = "Minimal alerts"
    overlay = "overlay on" if config.show_capture_overlay else "overlay off"
    return f"{startup} • {notifications} • {overlay}"


def maintenance_section_summary() -> str:
    return "Reset captures, logs, schedules, and local settings"