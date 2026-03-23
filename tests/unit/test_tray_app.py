from __future__ import annotations

import threading
from datetime import UTC, datetime
from types import SimpleNamespace

from selfsnap.models import AppConfig, CaptureRecord
from selfsnap.tray.app import (
    TrayRuntimeState,
    _any_dialog_open,
    _announce_record,
    _build_menu_items,
    _capture_now,
    _open_report_issue,
    _open_settings,
)
from selfsnap.tray.settings_window import SettingsDialogResult


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
        app_version="0.1.0",
        created_utc=now,
    )


def test_open_settings_does_not_persist_window_size_on_cancel(temp_paths, monkeypatch) -> None:
    saved_configs: list[AppConfig] = []

    monkeypatch.setattr(
        "selfsnap.tray.app.load_or_create_config",
        lambda _paths: AppConfig(
            capture_storage_root=str(temp_paths.default_capture_root),
            archive_storage_root=str(temp_paths.default_archive_root),
        ),
    )
    monkeypatch.setattr(
        "selfsnap.tray.app.show_settings_dialog",
        lambda _config, _paths: SettingsDialogResult(updated_config=None, window_size=(640, 520)),
    )
    monkeypatch.setattr(
        "selfsnap.tray.app.save_config", lambda _paths, config: saved_configs.append(config)
    )

    state = TrayRuntimeState(
        stop_event=threading.Event(),
        settings_dialog_open=threading.Event(),
        report_dialog_open=threading.Event(),
    )

    _open_settings(temp_paths, icon=SimpleNamespace(update_menu=lambda: None), state=state)

    assert saved_configs == []
    assert state.settings_dialog_open.is_set() is False


def test_open_settings_ignores_duplicate_requests(temp_paths, monkeypatch) -> None:
    dialog_calls: list[str] = []
    monkeypatch.setattr(
        "selfsnap.tray.app.load_or_create_config",
        lambda _paths: AppConfig(
            capture_storage_root=str(temp_paths.default_capture_root),
            archive_storage_root=str(temp_paths.default_archive_root),
        ),
    )
    monkeypatch.setattr(
        "selfsnap.tray.app.show_settings_dialog",
        lambda _config, _paths: (
            dialog_calls.append("dialog")
            or SettingsDialogResult(updated_config=None, window_size=(960, 760))
        ),
    )

    state = TrayRuntimeState(
        stop_event=threading.Event(),
        settings_dialog_open=threading.Event(),
        report_dialog_open=threading.Event(),
    )
    state.settings_dialog_open.set()

    _open_settings(temp_paths, icon=SimpleNamespace(update_menu=lambda: None), state=state)

    assert dialog_calls == []


def test_announce_record_suppresses_overlay_when_requested(monkeypatch) -> None:
    overlay_calls: list[str] = []
    monkeypatch.setattr(
        "selfsnap.tray.app._show_capture_overlay", lambda: overlay_calls.append("overlay")
    )

    config = AppConfig(
        capture_storage_root="C:\\captures",
        archive_storage_root="C:\\archive",
        show_capture_overlay=True,
    )

    _announce_record(SimpleNamespace(), config, _sample_record(), suppress_overlay=True)

    assert overlay_calls == []


def test_capture_now_runs_out_of_process_and_suppresses_ui_updates_with_settings_open(
    temp_paths, monkeypatch
) -> None:
    announced: list[str] = []
    menu_updates: list[str] = []
    notifications: list[str] = []
    record = _sample_record("record-2")

    monkeypatch.setattr(
        "selfsnap.tray.app.load_or_create_config",
        lambda _paths: AppConfig(
            capture_storage_root=str(temp_paths.default_capture_root),
            archive_storage_root=str(temp_paths.default_archive_root),
        ),
    )
    monkeypatch.setattr("selfsnap.tray.app.setup_logging", lambda _paths, _level: None)
    monkeypatch.setattr(
        "selfsnap.tray.app.resolve_manual_capture_background_invocation",
        lambda _paths: SimpleNamespace(
            command=lambda: ["pythonw.exe", "-m", "selfsnap", "capture"]
        ),
    )
    monkeypatch.setattr(
        "selfsnap.tray.app.run_background_command",
        lambda _spec: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr("selfsnap.tray.app._latest_record", lambda _paths: record)
    monkeypatch.setattr(
        "selfsnap.tray.app._announce_record",
        lambda *_args, **_kwargs: announced.append("announce"),
    )
    monkeypatch.setattr(
        "selfsnap.tray.app._show_notification",
        lambda *_args, **_kwargs: notifications.append("notify"),
    )

    icon = SimpleNamespace(update_menu=lambda: menu_updates.append("menu"))
    state = TrayRuntimeState(
        stop_event=threading.Event(),
        settings_dialog_open=threading.Event(),
        report_dialog_open=threading.Event(),
        last_announced_record_id=None,
    )
    state.settings_dialog_open.set()

    _capture_now(temp_paths, icon=icon, state=state)

    assert announced == []
    assert notifications == []
    assert menu_updates == []
    assert state.last_announced_record_id == record.record_id


def test_report_issue_menu_item_is_default_action(temp_paths, monkeypatch) -> None:
    class FakeMenu(list):
        def __init__(self, *items):
            super().__init__(items)

    class FakeMenuItem:
        def __init__(self, text, action, enabled=True, default=False):
            self.text = text
            self.action = action
            self.enabled = enabled
            self.default = default

    monkeypatch.setattr(
        "selfsnap.tray.app.load_or_create_config",
        lambda _paths: AppConfig(
            capture_storage_root=str(temp_paths.default_capture_root),
            archive_storage_root=str(temp_paths.default_archive_root),
        ),
    )

    state = TrayRuntimeState(
        stop_event=threading.Event(),
        settings_dialog_open=threading.Event(),
        report_dialog_open=threading.Event(),
    )
    items = _build_menu_items(
        SimpleNamespace(MenuItem=FakeMenuItem, Menu=FakeMenu), temp_paths, SimpleNamespace(), state
    )

    report_items = [
        item for item in items if not callable(item.text) and item.text == "Report Issue"
    ]
    assert len(report_items) == 1
    assert report_items[0].default is True


def test_report_issue_ignores_duplicate_requests(temp_paths, monkeypatch) -> None:
    report_calls: list[str] = []

    monkeypatch.setattr(
        "selfsnap.tray.app.show_report_issue_dialog", lambda _paths: report_calls.append("dialog")
    )

    state = TrayRuntimeState(
        stop_event=threading.Event(),
        settings_dialog_open=threading.Event(),
        report_dialog_open=threading.Event(),
    )
    state.report_dialog_open.set()

    _open_report_issue(temp_paths, icon=SimpleNamespace(update_menu=lambda: None), state=state)

    assert report_calls == []


def test_report_issue_can_open_while_settings_is_open(temp_paths, monkeypatch) -> None:
    report_calls: list[str] = []
    monkeypatch.setattr(
        "selfsnap.tray.app.show_report_issue_dialog", lambda _paths: report_calls.append("dialog")
    )

    state = TrayRuntimeState(
        stop_event=threading.Event(),
        settings_dialog_open=threading.Event(),
        report_dialog_open=threading.Event(),
    )
    state.settings_dialog_open.set()

    _open_report_issue(temp_paths, icon=SimpleNamespace(update_menu=lambda: None), state=state)

    assert report_calls == ["dialog"]


def test_settings_can_open_while_report_issue_is_open(temp_paths, monkeypatch) -> None:
    settings_calls: list[str] = []
    monkeypatch.setattr(
        "selfsnap.tray.app.load_or_create_config",
        lambda _paths: AppConfig(
            capture_storage_root=str(temp_paths.default_capture_root),
            archive_storage_root=str(temp_paths.default_archive_root),
        ),
    )
    monkeypatch.setattr(
        "selfsnap.tray.app.show_settings_dialog",
        lambda _config, _paths: (
            settings_calls.append("dialog")
            or SettingsDialogResult(updated_config=None, window_size=(960, 760))
        ),
    )

    state = TrayRuntimeState(
        stop_event=threading.Event(),
        settings_dialog_open=threading.Event(),
        report_dialog_open=threading.Event(),
    )
    state.report_dialog_open.set()

    _open_settings(temp_paths, icon=SimpleNamespace(update_menu=lambda: None), state=state)

    assert settings_calls == ["dialog"]


def test_any_dialog_open_is_true_when_either_dialog_is_open() -> None:
    state = TrayRuntimeState(
        stop_event=threading.Event(),
        settings_dialog_open=threading.Event(),
        report_dialog_open=threading.Event(),
    )

    assert _any_dialog_open(state) is False
    state.settings_dialog_open.set()
    assert _any_dialog_open(state) is True
    state.settings_dialog_open.clear()
    state.report_dialog_open.set()
    assert _any_dialog_open(state) is True


def test_tray_menu_contains_restart_reinstall_and_uninstall_before_exit(temp_paths, monkeypatch) -> None:
    class FakeMenu(list):
        def __init__(self, *items):
            super().__init__(items)

    class FakeMenuItem:
        def __init__(self, text, action, enabled=True, default=False):
            self.text = text
            self.action = action
            self.enabled = enabled
            self.default = default

    monkeypatch.setattr(
        "selfsnap.tray.app.load_or_create_config",
        lambda _paths: AppConfig(
            capture_storage_root=str(temp_paths.default_capture_root),
            archive_storage_root=str(temp_paths.default_archive_root),
        ),
    )

    state = TrayRuntimeState(
        stop_event=threading.Event(),
        settings_dialog_open=threading.Event(),
        report_dialog_open=threading.Event(),
    )
    items = _build_menu_items(
        SimpleNamespace(MenuItem=FakeMenuItem, Menu=FakeMenu), temp_paths, SimpleNamespace(), state
    )

    labels = [item.text for item in items if not callable(item.text)]
    assert labels[-4:] == ["Restart", "Reinstall", "Uninstall", "Exit"]

    submenu_by_label = {item.text: item.action for item in items if not callable(item.text)}
    assert [item.text for item in submenu_by_label["Restart"]] == ["Restart SelfSnap"]
    assert [item.text for item in submenu_by_label["Reinstall"]] == [
        "From Local Source",
        "From Source and Update",
    ]
    assert [item.text for item in submenu_by_label["Uninstall"]] == [
        "Keep User Data",
        "Remove All User Data",
    ]
