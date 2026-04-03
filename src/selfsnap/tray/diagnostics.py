from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from selfsnap.models import AppConfig, CaptureRecord, OutcomeCategory
from selfsnap.paths import AppPaths
from selfsnap.ui_labels import (
    capture_mode_label,
    enabled_disabled_label,
    image_format_label,
    notification_mode_label,
    on_off_label,
    retention_policy_label,
    scheduler_sync_state_label,
    storage_preset_label,
)


@dataclass(slots=True)
class DiagnosticSummary:
    headline: str
    detail: str
    tone: str = "neutral"


def format_local_timestamp(utc_text: str | None) -> str:
    if not utc_text:
        return "(unknown time)"
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


def scheduler_sync_summary(config: AppConfig) -> DiagnosticSummary:
    if not config.first_run_completed:
        return DiagnosticSummary(
            headline="Setup Required",
            detail=(
                "Complete first-run setup before SelfSnap can register coarse schedules with "
                "Windows Task Scheduler."
            ),
            tone="neutral",
        )
    if config.scheduler_sync_failed():
        return DiagnosticSummary(
            headline=scheduler_sync_state_label(config.scheduler_sync_state),
            detail=(
                config.scheduler_sync_message
                or "Task Scheduler sync previously failed. Scheduled captures stay blocked until "
                "the next successful sync."
            ),
            tone="warn",
        )
    detail = "Windows Task Scheduler registrations are synchronized."
    if not config.app_enabled:
        detail = (
            "Scheduler sync is healthy. Scheduled captures stay paused until the tray is enabled."
        )
    return DiagnosticSummary(
        headline=scheduler_sync_state_label(config.scheduler_sync_state),
        detail=detail,
        tone="good",
    )


def last_activity_summary(record: CaptureRecord | None) -> DiagnosticSummary:
    if record is None:
        return DiagnosticSummary(
            headline="No captures recorded",
            detail=(
                "Use Capture Now from the tray to validate storage, "
                "notifications, and overlay behavior."
            ),
            tone="neutral",
        )
    timestamp_text = format_local_timestamp(record.started_utc or record.created_utc)
    trigger_text = record.trigger_source.replace("_", " ")
    detail_parts = [
        trigger_text,
        record.outcome_category,
        "file saved" if record.file_present else "no output file",
    ]
    if record.schedule_id:
        detail_parts.append(f"schedule {record.schedule_id}")
    tone = "neutral"
    if record.outcome_category == OutcomeCategory.SUCCESS.value:
        tone = "good"
    elif record.outcome_category in {OutcomeCategory.FAILED.value, OutcomeCategory.MISSED.value}:
        tone = "warn"
    return DiagnosticSummary(
        headline=f"{record.outcome_code} at {timestamp_text}",
        detail=" | ".join(detail_parts),
        tone=tone,
    )


def storage_summary(config: AppConfig, paths: AppPaths) -> DiagnosticSummary:
    capture_root = config.capture_storage_root.strip()
    archive_root = config.archive_storage_root.strip()
    resolved_capture_root = str(paths.resolve_capture_root(config)) if capture_root else "(empty)"
    resolved_archive_root = str(paths.resolve_archive_root(config)) if archive_root else "(empty)"
    return DiagnosticSummary(
        headline=f"{storage_preset_label(config.storage_preset)} preset",
        detail=f"Capture: {resolved_capture_root}\nArchive: {resolved_archive_root}",
        tone="good" if config.storage_preset != "custom" else "neutral",
    )


def retention_summary(config: AppConfig) -> DiagnosticSummary:
    headline = retention_policy_label(
        config.retention_mode,
        config.retention_days,
        config.purge_enabled,
        config.retention_grace_days,
    )
    if config.retention_mode == "keep_forever":
        detail = (
            "Automatic archival and purge are off. Files stay in the "
            "capture root until you move them."
        )
    else:
        detail = f"Moves captures to archive after {config.retention_days} day(s)."
        if config.purge_enabled:
            detail += f" Purges archived files {config.retention_grace_days} day(s) later."
        else:
            detail += " Archived files remain available until you remove them manually."
    return DiagnosticSummary(headline=headline, detail=detail, tone="neutral")


def notification_summary(config: AppConfig) -> DiagnosticSummary:
    headline = notification_mode_label(
        config.notify_on_failed_or_missed,
        config.notify_on_every_capture,
    )
    detail = (
        f"Latest tray status {on_off_label(config.show_last_capture_status)} | "
        f"Overlay {on_off_label(config.show_capture_overlay)}"
    )
    return DiagnosticSummary(headline=headline, detail=detail, tone="neutral")


def operational_summary(config: AppConfig, paths: AppPaths) -> DiagnosticSummary:
    headline = (
        f"Tray {enabled_disabled_label(config.app_enabled)} | "
        f"Startup {on_off_label(config.start_tray_on_login)} | "
        f"Wake {on_off_label(config.wake_for_scheduled_captures)}"
    )
    detail = (
        f"Capture: {capture_mode_label(config.capture_mode)} / "
        f"{image_format_label(config.image_format)} @ {config.image_quality}\n"
        f"Config: {paths.config_path}\n"
        f"DB: {paths.db_path}\n"
        f"Logs: {paths.log_path}"
    )
    return DiagnosticSummary(headline=headline, detail=detail, tone="neutral")


def tray_state_label(config: AppConfig) -> str:
    if not config.first_run_completed:
        return "State: setup required"
    if not config.app_enabled:
        return "State: disabled"
    if config.scheduler_sync_failed():
        return "State: enabled, scheduler sync failed"
    return "State: enabled"


def tray_warning_label(config: AppConfig) -> str | None:
    if not config.scheduler_sync_failed():
        return None
    return "Warning: scheduler sync failed - open Settings"


def tray_title(config: AppConfig) -> str:
    if config.scheduler_sync_failed():
        return "SelfSnap Win11 - scheduler sync failed"
    if not config.first_run_completed:
        return "SelfSnap Win11 - setup required"
    return "SelfSnap Win11"
