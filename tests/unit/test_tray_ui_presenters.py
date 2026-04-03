from __future__ import annotations

from datetime import UTC, datetime

from selfsnap.models import AppConfig, CaptureRecord
from selfsnap.tray.schedule_editor import default_draft
from selfsnap.tray.ui_presenters import (
    disclosure_button_label,
    format_latest_record_label,
    format_local_timestamp,
    maintenance_section_summary,
    notifications_section_summary,
    settings_hero_state,
    storage_section_summary,
    tray_icon_title,
    tray_scheduler_warning_label,
    tray_state_label,
    tray_toggle_label,
)


def _sample_record(record_id: str = "record-1") -> CaptureRecord:
    now = datetime.now(UTC).isoformat()
    return CaptureRecord(
        record_id=record_id,
        trigger_source="manual",
        schedule_id=None,
        planned_local_ts=None,
        started_utc=now,
        finished_utc=now,
        outcome_category="success",
        outcome_code="capture_saved",
        image_path="C:\\captures\\cap.png",
        file_present=True,
        image_sha256="abc",
        monitor_count=1,
        composite_width=10,
        composite_height=10,
        file_bytes=10,
        error_code=None,
        error_message=None,
        archived=False,
        archived_at_utc=None,
        retention_deleted_at_utc=None,
        app_version="0.8.0",
        created_utc=now,
    )


def test_format_local_timestamp_treats_naive_as_utc() -> None:
    naive = "2026-04-03T14:03:00"
    explicit_utc = "2026-04-03T14:03:00+00:00"

    assert format_local_timestamp(naive) == format_local_timestamp(explicit_utc)


def test_format_latest_record_label_handles_missing_record() -> None:
    assert format_latest_record_label(None) == "Latest capture: none yet"
    assert "capture_saved" in format_latest_record_label(_sample_record())


def test_tray_labels_follow_current_runtime_state() -> None:
    config = AppConfig(capture_storage_root="C:\\cap", archive_storage_root="C:\\arc")

    assert tray_state_label(config) == "Status: setup required"
    assert tray_toggle_label(config) == "Enable Scheduled Captures"
    assert tray_scheduler_warning_label(config) is None

    config.first_run_completed = True
    assert tray_state_label(config) == "Status: paused"
    assert tray_icon_title(config) == "SelfSnap Win11 - paused"

    config.app_enabled = True
    assert tray_state_label(config) == "Status: running"
    assert tray_toggle_label(config) == "Pause Scheduled Captures"
    assert tray_icon_title(config) == "SelfSnap Win11"

    config.mark_scheduler_sync_failed("Task Scheduler unavailable")
    assert tray_state_label(config) == "Status: running, scheduler needs attention"
    assert tray_scheduler_warning_label(config) == "Scheduler sync failed. Open Settings."
    assert tray_icon_title(config) == "SelfSnap Win11 - scheduler needs attention"


def test_settings_hero_and_section_summaries_reflect_focus_layout() -> None:
    config = AppConfig(
        capture_storage_root="C:\\cap",
        archive_storage_root="C:\\arc",
        first_run_completed=True,
        app_enabled=False,
        storage_preset="local_pictures",
        retention_mode="keep_days",
        retention_days=14,
        start_tray_on_login=False,
        notify_on_failed_or_missed=False,
        notify_on_every_capture=True,
        show_capture_overlay=True,
    )

    hero = settings_hero_state(config, [default_draft(datetime(2026, 4, 3, 9, 0, 0))], "Latest capture: none yet")

    assert hero.headline == "Paused"
    assert hero.message == "Scheduled captures are off. Capture now still works."
    assert "Schedules: 1 schedule • 1 enabled" in hero.details
    assert storage_section_summary(config) == "Local Pictures • Archive After N Days (14 days)"
    assert notifications_section_summary(config) == "Starts manually • Alerts on every capture • overlay on"
    assert maintenance_section_summary() == "Reset captures, logs, schedules, and local settings"
    assert disclosure_button_label("Storage & Output", expanded=False) == "Show storage & output"
    assert disclosure_button_label("Storage & Output", expanded=True) == "Hide storage & output"