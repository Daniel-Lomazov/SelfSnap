from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import threading

from selfsnap.models import AppConfig, CaptureRecord
from selfsnap.tray.app import TrayRuntimeState, _announce_record, _open_settings
from selfsnap.tray.settings_window import SettingsDialogResult


def test_open_settings_does_not_persist_window_size_on_cancel(temp_paths, monkeypatch) -> None:
    saved_configs: list[AppConfig] = []

    monkeypatch.setattr("selfsnap.tray.app.load_or_create_config", lambda _paths: AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
    ))
    monkeypatch.setattr(
        "selfsnap.tray.app.show_settings_dialog",
        lambda _config, _paths: SettingsDialogResult(updated_config=None, window_size=(640, 520)),
    )
    monkeypatch.setattr("selfsnap.tray.app.save_config", lambda _paths, config: saved_configs.append(config))

    state = TrayRuntimeState(stop_event=threading.Event(), settings_dialog_open=threading.Event())

    _open_settings(temp_paths, icon=SimpleNamespace(update_menu=lambda: None), state=state)

    assert saved_configs == []
    assert state.settings_dialog_open.is_set() is False


def test_announce_record_suppresses_overlay_when_requested(monkeypatch) -> None:
    overlay_calls: list[str] = []
    monkeypatch.setattr("selfsnap.tray.app._show_capture_overlay", lambda: overlay_calls.append("overlay"))

    config = AppConfig(
        capture_storage_root="C:\\captures",
        archive_storage_root="C:\\archive",
        show_capture_overlay=True,
    )
    record = CaptureRecord(
        record_id="record-1",
        trigger_source="manual",
        schedule_id=None,
        planned_local_ts=None,
        started_utc=datetime.now(timezone.utc).isoformat(),
        finished_utc=datetime.now(timezone.utc).isoformat(),
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
        app_version="0.1.0",
        created_utc=datetime.now(timezone.utc).isoformat(),
    )

    _announce_record(SimpleNamespace(), config, record, suppress_overlay=True)

    assert overlay_calls == []
