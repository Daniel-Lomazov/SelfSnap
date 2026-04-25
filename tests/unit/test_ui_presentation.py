from __future__ import annotations

from dataclasses import replace

from selfsnap.models import AppConfig
from selfsnap.ui.presentation import (
    application_title,
    latest_capture_label,
    maintenance_summary_text,
    record_message,
    scheduler_status_detail,
    settings_page_subtitle,
    settings_window_title,
    settings_header_status,
    storage_summary_text,
    tray_icon_title,
    tray_state_label,
    tray_status_summary_label,
    tray_toggle_enabled_label,
    tray_warning_label,
    visibility_summary_text,
)
from selfsnap.version import __version__


def _config() -> AppConfig:
    return AppConfig(
        capture_storage_root="C:\\captures",
        archive_storage_root="C:\\archive",
        first_run_completed=True,
    )


def test_settings_header_status_tracks_manual_enabled_and_warning_states() -> None:
    base = _config()

    assert settings_header_status(base) == ("Manual capture only", "neutral")
    assert settings_header_status(replace(base, app_enabled=True)) == (
        "Scheduled capture enabled",
        "accent",
    )
    assert settings_header_status(replace(base, scheduler_sync_state="failed")) == (
        "Scheduler sync needs attention",
        "warning",
    )


def test_scheduler_status_detail_prefers_saved_message() -> None:
    failed = replace(
        _config(), scheduler_sync_state="failed", scheduler_sync_message="Access denied"
    )

    assert scheduler_status_detail(failed) == "Task Scheduler last reported an issue: Access denied"
    assert scheduler_status_detail(_config()) is None


def test_storage_summary_text_formats_retention_capture_and_purge() -> None:
    text = storage_summary_text(
        storage_preset="custom",
        retention_mode="keep_days",
        retention_days="45",
        capture_mode="per_monitor",
        image_format="jpeg",
        image_quality="92",
        purge_enabled=True,
        retention_grace_days="14",
    )

    assert text == (
        "Custom Folder • Archives after 45 days • Per Monitor JPEG 92% • Purges after 14-day grace"
    )


def test_visibility_summary_text_reflects_notification_level() -> None:
    text = visibility_summary_text(
        start_tray_on_login=True,
        wake_for_scheduled_captures=False,
        show_last_capture_status=True,
        notify_on_failed_or_missed=False,
        notify_on_every_capture=True,
        show_capture_overlay=False,
    )

    assert text == (
        "Launches on sign-in • Wake requests off • Tray status visible • "
        "All capture notifications • Overlay off"
    )


def test_tray_presentation_helpers_preserve_existing_labels() -> None:
    base = _config()
    failed = replace(base, app_enabled=True, scheduler_sync_state="failed")

    assert application_title() == f"SelfSnap Win11 v{__version__}"
    assert settings_page_subtitle() == (
        "Manage capture behavior, storage, schedules, diagnostics, and maintenance."
    )
    assert settings_window_title() == f"SelfSnap Settings v{__version__}"
    assert tray_state_label(base) == "Scheduled captures paused"
    assert tray_state_label(failed) == "Scheduled captures on"
    assert tray_warning_label(base) is None
    assert tray_warning_label(failed) == "Scheduler needs attention - open Settings"
    assert tray_icon_title(base) == f"SelfSnap Win11 v{__version__}"
    assert tray_icon_title(failed) == f"SelfSnap Win11 v{__version__} - scheduler sync failed"
    assert tray_toggle_enabled_label(True) == "Pause Scheduled Captures"
    assert tray_toggle_enabled_label(False) == "Resume Scheduled Captures"
    assert latest_capture_label("capture_saved", "LOCAL") == "Last capture: Saved at LOCAL"
    assert tray_status_summary_label("Scheduled captures on") == "Scheduled captures on"
    assert (
        tray_status_summary_label(
            "Scheduled captures on",
            "Last capture: Saved at LOCAL",
        )
        == "Scheduled captures on • Last capture: Saved at LOCAL"
    )
    assert record_message("capture_saved", "sched_1") == "capture_saved (sched_1)"
    assert maintenance_summary_text().startswith("Reset capture history")
