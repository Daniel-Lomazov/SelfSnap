from __future__ import annotations

from datetime import UTC, datetime

from selfsnap.models import AppConfig, CaptureRecord
from selfsnap.ui.diagnostics import (
    format_local_timestamp,
    last_activity_summary,
    notification_summary,
    operational_summary,
    retention_summary,
    scheduler_sync_summary,
    storage_summary,
)


def _record(
    outcome_category: str = "success", outcome_code: str = "capture_saved"
) -> CaptureRecord:
    now = datetime(2026, 4, 3, 14, 3, 0, tzinfo=UTC).isoformat()
    return CaptureRecord(
        record_id="record-1",
        trigger_source="manual",
        schedule_id=None,
        planned_local_ts=None,
        started_utc=now,
        finished_utc=now,
        outcome_category=outcome_category,
        outcome_code=outcome_code,
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
        app_version="1.0.1",
        created_utc=now,
    )


def test_format_local_timestamp_treats_naive_as_utc() -> None:
    naive = "2026-04-03T14:03:00"
    explicit_utc = "2026-04-03T14:03:00+00:00"

    assert format_local_timestamp(naive) == format_local_timestamp(explicit_utc)


def test_scheduler_and_storage_summaries_surface_health_and_paths(temp_paths) -> None:
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
        first_run_completed=True,
        app_enabled=True,
    )

    scheduler = scheduler_sync_summary(config)
    storage = storage_summary(config, temp_paths)

    assert scheduler.headline == "Healthy"
    assert "synchronized" in scheduler.detail
    assert storage.headline == "Local Pictures preset"
    assert str(temp_paths.default_capture_root) in storage.detail
    assert str(temp_paths.default_archive_root) in storage.detail


def test_last_activity_summary_warns_for_failed_record() -> None:
    summary = last_activity_summary(
        _record(outcome_category="failed", outcome_code="scheduler_sync_error")
    )

    assert summary.tone == "warn"
    assert "scheduler_sync_error at" in summary.headline
    assert "failed" in summary.detail


def test_notification_retention_and_operational_summaries_are_power_user_facing(temp_paths) -> None:
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
        first_run_completed=True,
        app_enabled=False,
        retention_mode="keep_days",
        retention_days=14,
        purge_enabled=True,
        retention_grace_days=7,
        notify_on_failed_or_missed=True,
        notify_on_every_capture=False,
        show_last_capture_status=True,
        show_capture_overlay=True,
        start_tray_on_login=True,
        wake_for_scheduled_captures=False,
        capture_mode="composite",
        image_format="png",
    )

    notifications = notification_summary(config)
    retention = retention_summary(config)
    operations = operational_summary(config, temp_paths)

    assert notifications.headline == "Failures and misses only"
    assert "Overlay On" in notifications.detail
    assert retention.headline == "Archive after 14 days, purge 7 grace days later"
    assert "Purges archived files 7 day(s) later" in retention.detail
    assert "Tray Disabled" in operations.headline
    assert str(temp_paths.config_path) in operations.detail