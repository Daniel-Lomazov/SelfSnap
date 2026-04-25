from __future__ import annotations

import threading
from datetime import UTC, datetime
from types import SimpleNamespace

from selfsnap.models import AppConfig, CaptureRecord, Schedule
from selfsnap.tray.app import (
    TrayRuntimeState,
    _announce_record,
    _any_dialog_open,
    _build_menu_items,
    _capture_now,
    _check_for_updates,
    _format_local_timestamp,
    _latest_label,
    _open_report_issue,
    _open_settings,
    _reinstall_selfsnap,
    _restart_selfsnap,
    _run_high_frequency_scheduler,
    _toggle_enabled,
)
from selfsnap.tray.settings_window import SettingsDialogResult
from selfsnap.window_sizing import DEFAULT_SETTINGS_WINDOW_HEIGHT, DEFAULT_SETTINGS_WINDOW_WIDTH


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


def _state() -> TrayRuntimeState:
    now = datetime.now(UTC)
    return TrayRuntimeState(
        stop_event=threading.Event(),
        settings_dialog_open=threading.Event(),
        report_dialog_open=threading.Event(),
        last_high_frequency_check=now,
        next_housekeeping_at=now,
    )


def _menu_label(item) -> str:
    return item.text(None) if callable(item.text) else item.text


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

    state = _state()

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
            or SettingsDialogResult(
                updated_config=None,
                window_size=(DEFAULT_SETTINGS_WINDOW_WIDTH, DEFAULT_SETTINGS_WINDOW_HEIGHT),
            )
        ),
    )

    state = _state()
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
    state = _state()
    state.last_announced_record_id = None
    state.settings_dialog_open.set()

    _capture_now(temp_paths, icon=icon, state=state)

    assert announced == []
    assert notifications == []
    assert menu_updates == []
    assert state.last_announced_record_id == record.record_id


def test_settings_menu_item_is_default_action(temp_paths, monkeypatch) -> None:
    class FakeMenu(list):
        SEPARATOR = None

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

    state = _state()
    items = _build_menu_items(
        SimpleNamespace(MenuItem=FakeMenuItem, Menu=FakeMenu), temp_paths, SimpleNamespace(), state
    )

    settings_items = [
        item
        for item in items
        if item is not None and not callable(item.text) and item.text == "Settings"
    ]
    assert len(settings_items) == 1
    assert settings_items[0].default is True


def test_format_local_timestamp_treats_naive_as_utc() -> None:
    naive = "2026-04-03T14:03:00"
    explicit_utc = "2026-04-03T14:03:00+00:00"

    assert _format_local_timestamp(naive) == _format_local_timestamp(explicit_utc)


def test_latest_label_prefers_started_utc_when_present(temp_paths, monkeypatch) -> None:
    record = _sample_record("record-latest")
    record.started_utc = "2026-04-03T14:03:00+00:00"
    record.created_utc = "2026-04-03T14:04:00+00:00"

    monkeypatch.setattr("selfsnap.tray.app.ensure_database", lambda _path: None)

    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    seen: list[str] = []
    monkeypatch.setattr("selfsnap.tray.app.connect", lambda _path: _Conn())
    monkeypatch.setattr("selfsnap.tray.app.get_latest_record", lambda _conn: record)
    monkeypatch.setattr(
        "selfsnap.tray.app._format_local_timestamp",
        lambda value: seen.append(value) or "LOCAL_TIME",
    )

    label = _latest_label(temp_paths)

    assert seen == ["2026-04-03T14:03:00+00:00"]
    assert label == "Last capture: Saved at LOCAL_TIME"


def test_report_issue_ignores_duplicate_requests(temp_paths, monkeypatch) -> None:
    report_calls: list[str] = []

    monkeypatch.setattr(
        "selfsnap.tray.app.show_report_issue_dialog", lambda _paths: report_calls.append("dialog")
    )

    state = _state()
    state.report_dialog_open.set()

    _open_report_issue(temp_paths, icon=SimpleNamespace(update_menu=lambda: None), state=state)

    assert report_calls == []


def test_report_issue_can_open_while_settings_is_open(temp_paths, monkeypatch) -> None:
    report_calls: list[str] = []
    monkeypatch.setattr(
        "selfsnap.tray.app.show_report_issue_dialog", lambda _paths: report_calls.append("dialog")
    )

    state = _state()
    state.settings_dialog_open.set()

    _open_report_issue(temp_paths, icon=SimpleNamespace(update_menu=lambda: None), state=state)

    assert report_calls == ["dialog"]


def test_restart_selfsnap_schedules_relaunch_after_current_process_exits(
    temp_paths, monkeypatch
) -> None:
    exited: list[str] = []
    monkeypatch.setattr(
        "selfsnap.tray.app.schedule_tray_relaunch_after_exit",
        lambda _paths, wait_for_process_id: wait_for_process_id > 0,
    )
    monkeypatch.setattr(
        "selfsnap.tray.app._exit",
        lambda _icon, _stop_event: exited.append("exit"),
    )
    monkeypatch.setattr(
        "selfsnap.tray.app._show_error_dialog", lambda *_args: exited.append("error")
    )

    _restart_selfsnap(temp_paths, icon=SimpleNamespace(), state=_state())

    assert exited == ["exit"]


def test_reinstall_selfsnap_runs_script_without_immediate_relaunch_and_exits_on_success(
    temp_paths, monkeypatch
) -> None:
    prompts: list[str] = []
    scheduled: list[int] = []
    exits: list[str] = []
    invocation_args: list[tuple[bool, bool]] = []

    monkeypatch.setattr("selfsnap.tray.app._ask_confirmation", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        "selfsnap.tray.app.resolve_reinstall_invocation",
        lambda _paths, update_source, relaunch_tray, target_tag=None: (
            invocation_args.append((update_source, relaunch_tray)) or object()
        ),
    )
    monkeypatch.setattr("selfsnap.tray.app.run_lifecycle_script_and_check", lambda _spec: True)
    monkeypatch.setattr(
        "selfsnap.tray.app.schedule_tray_relaunch_after_exit",
        lambda _paths, wait_for_process_id: scheduled.append(wait_for_process_id) or True,
    )
    monkeypatch.setattr(
        "selfsnap.tray.app._exit",
        lambda _icon, _stop_event: exits.append("exit"),
    )
    monkeypatch.setattr(
        "selfsnap.tray.app._show_error_dialog",
        lambda title, message: prompts.append(f"{title}: {message}"),
    )

    _reinstall_selfsnap(temp_paths, icon=SimpleNamespace(), state=_state(), update_source=False)

    assert invocation_args == [(False, False)]
    assert len(scheduled) == 1
    assert exits == ["exit"]
    assert prompts == []


def test_reinstall_selfsnap_keeps_current_tray_running_when_relaunch_schedule_fails(
    temp_paths, monkeypatch
) -> None:
    prompts: list[str] = []
    exits: list[str] = []

    monkeypatch.setattr("selfsnap.tray.app._ask_confirmation", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        "selfsnap.tray.app.resolve_reinstall_invocation", lambda *_args, **_kwargs: object()
    )
    monkeypatch.setattr("selfsnap.tray.app.run_lifecycle_script_and_check", lambda _spec: True)
    monkeypatch.setattr(
        "selfsnap.tray.app.schedule_tray_relaunch_after_exit",
        lambda _paths, wait_for_process_id: False,
    )
    monkeypatch.setattr(
        "selfsnap.tray.app._exit",
        lambda _icon, _stop_event: exits.append("exit"),
    )
    monkeypatch.setattr(
        "selfsnap.tray.app._show_error_dialog",
        lambda title, message: prompts.append(f"{title}: {message}"),
    )

    _reinstall_selfsnap(temp_paths, icon=SimpleNamespace(), state=_state(), update_source=True)

    assert exits == []
    assert len(prompts) == 1


def test_check_for_updates_schedules_relaunch_after_successful_install(
    temp_paths, monkeypatch
) -> None:
    invocation_args: list[tuple[bool, bool, str | None]] = []
    scheduled: list[int] = []
    exits: list[str] = []

    monkeypatch.setattr("selfsnap.update_checker.fetch_latest_release_tag", lambda _repo: "v99.0.0")
    monkeypatch.setattr("selfsnap.tray.app._ask_confirmation", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        "selfsnap.tray.app.resolve_reinstall_invocation",
        lambda _paths, update_source, relaunch_tray, target_tag=None: (
            invocation_args.append((update_source, relaunch_tray, target_tag)) or object()
        ),
    )
    monkeypatch.setattr("selfsnap.tray.app.run_lifecycle_script_and_check", lambda _spec: True)
    monkeypatch.setattr(
        "selfsnap.tray.app.schedule_tray_relaunch_after_exit",
        lambda _paths, wait_for_process_id: scheduled.append(wait_for_process_id) or True,
    )
    monkeypatch.setattr(
        "selfsnap.tray.app._exit",
        lambda _icon, _stop_event: exits.append("exit"),
    )
    monkeypatch.setattr("selfsnap.tray.app._show_error_dialog", lambda *_args, **_kwargs: None)

    _check_for_updates(temp_paths, icon=SimpleNamespace(), state=_state())

    assert invocation_args == [(True, False, "v99.0.0")]
    assert len(scheduled) == 1
    assert exits == ["exit"]


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
            or SettingsDialogResult(
                updated_config=None,
                window_size=(DEFAULT_SETTINGS_WINDOW_WIDTH, DEFAULT_SETTINGS_WINDOW_HEIGHT),
            )
        ),
    )

    state = _state()
    state.report_dialog_open.set()

    _open_settings(temp_paths, icon=SimpleNamespace(update_menu=lambda: None), state=state)

    assert settings_calls == ["dialog"]


def test_any_dialog_open_is_true_when_either_dialog_is_open() -> None:
    state = _state()

    assert _any_dialog_open(state) is False
    state.settings_dialog_open.set()
    assert _any_dialog_open(state) is True
    state.settings_dialog_open.clear()
    state.report_dialog_open.set()
    assert _any_dialog_open(state) is True


def test_tray_menu_groups_browse_and_app_actions_under_submenus(temp_paths, monkeypatch) -> None:
    class FakeMenu(list):
        SEPARATOR = None

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
            first_run_completed=True,
        ),
    )

    state = _state()
    items = _build_menu_items(
        SimpleNamespace(MenuItem=FakeMenuItem, Menu=FakeMenu), temp_paths, SimpleNamespace(), state
    )

    labels = [_menu_label(item) for item in items if item is not None]
    assert labels == [
        "Scheduled captures paused • Last capture: none yet",
        "Capture Now",
        "Resume Scheduled Captures",
        "Settings",
        "Browse",
        "App",
    ]

    submenu_by_label = {_menu_label(item): item.action for item in items if item is not None}

    browse_labels = [_menu_label(item) for item in submenu_by_label["Browse"]]
    assert browse_labels == [
        "Open Last Capture",
        "Open Capture Folder",
        "Recent Captures",
        "Statistics",
    ]

    app_labels = [_menu_label(item) for item in submenu_by_label["App"]]
    assert app_labels == [
        "Check for Updates",
        "Report Issue",
        "Repair or Reinstall",
        "Restart",
        "Uninstall",
        "Exit",
    ]

    uninstall_submenu = {
        _menu_label(item): item.action for item in submenu_by_label["App"] if item is not None
    }["Uninstall"]
    assert [_menu_label(item) for item in uninstall_submenu] == [
        "Keep User Data",
        "Remove All User Data",
    ]


def test_tray_menu_status_row_omits_latest_when_preference_disabled(
    temp_paths, monkeypatch
) -> None:
    class FakeMenu(list):
        SEPARATOR = None

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
            first_run_completed=True,
            show_last_capture_status=False,
        ),
    )

    items = _build_menu_items(
        SimpleNamespace(MenuItem=FakeMenuItem, Menu=FakeMenu),
        temp_paths,
        SimpleNamespace(),
        _state(),
    )

    labels = [_menu_label(item) for item in items if item is not None]
    assert labels[0] == "Scheduled captures paused"


def test_toggle_enabled_uses_refresh_menu_callback(temp_paths, monkeypatch) -> None:
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
        app_enabled=False,
        first_run_completed=True,
    )
    refresh_calls: list[str] = []
    icon_updates: list[str] = []
    sync_calls: list[str] = []

    monkeypatch.setattr("selfsnap.tray.app.load_or_create_config", lambda _paths: config)
    monkeypatch.setattr("selfsnap.tray.app.save_config", lambda _paths, _config: None)
    monkeypatch.setattr(
        "selfsnap.tray.app.sync_scheduler_from_config",
        lambda _paths, emit_console=False: sync_calls.append("sync"),
    )

    icon = SimpleNamespace(update_menu=lambda: icon_updates.append("menu"))
    _toggle_enabled(temp_paths, icon, refresh_menu=lambda: refresh_calls.append("refresh"))

    assert config.app_enabled is True
    assert sync_calls == ["sync"]
    assert refresh_calls == ["refresh"]
    assert icon_updates == []


def test_toggle_enabled_first_run_cancel_uses_refresh_menu_callback(
    temp_paths, monkeypatch
) -> None:
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
        app_enabled=False,
        first_run_completed=False,
    )
    refresh_calls: list[str] = []
    icon_updates: list[str] = []
    sync_calls: list[str] = []

    monkeypatch.setattr("selfsnap.tray.app.load_or_create_config", lambda _paths: config)
    monkeypatch.setattr("selfsnap.tray.app.show_first_run_dialog", lambda _config, _paths: None)
    monkeypatch.setattr("selfsnap.tray.app.save_config", lambda _paths, _config: None)
    monkeypatch.setattr(
        "selfsnap.tray.app.sync_scheduler_from_config",
        lambda _paths, emit_console=False: sync_calls.append("sync"),
    )

    icon = SimpleNamespace(update_menu=lambda: icon_updates.append("menu"))
    _toggle_enabled(temp_paths, icon, refresh_menu=lambda: refresh_calls.append("refresh"))

    assert config.app_enabled is False
    assert sync_calls == []
    assert refresh_calls == ["refresh"]
    assert icon_updates == []


def test_check_for_updates_when_installed_is_newer_shows_installed_as_latest(
    temp_paths, monkeypatch
) -> None:
    from selfsnap.version import __version__

    shown: list[tuple[str, str]] = []

    monkeypatch.setattr("selfsnap.update_checker.fetch_latest_release_tag", lambda _repo: "v1.0.0")
    monkeypatch.setattr("selfsnap.tray.app._show_info_dialog", lambda t, m: shown.append((t, m)))
    monkeypatch.setattr("selfsnap.tray.app._show_error_dialog", lambda *_args, **_kwargs: None)

    state = _state()
    _check_for_updates(temp_paths, icon=SimpleNamespace(), state=state)

    assert len(shown) == 1
    title, message = shown[0]
    assert title == "Check for Updates"
    assert f"Installed: v{__version__}" in message
    assert f"Latest:    v{__version__}" in message


def test_run_high_frequency_scheduler_launches_due_occurrences(temp_paths, monkeypatch) -> None:
    launched: list[list[str]] = []
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
        first_run_completed=True,
        app_enabled=True,
        schedules=[
            Schedule(
                schedule_id="fast",
                label="Fast",
                interval_value=1,
                interval_unit="minute",
                start_date_local="2026-03-23",
                start_time_local="10:00:00",
            )
        ],
    )

    monkeypatch.setattr("selfsnap.tray.app.load_or_create_config", lambda _paths: config)
    monkeypatch.setattr(
        "selfsnap.tray.app.resolve_worker_background_invocation",
        lambda _paths, schedule_id, planned_local_ts: SimpleNamespace(
            command=lambda: ["pythonw.exe", "-m", "selfsnap", "capture", planned_local_ts],
            working_directory=str(temp_paths.root),
        ),
    )
    monkeypatch.setattr(
        "selfsnap.tray.app.launch_background", lambda spec: launched.append(spec.command())
    )

    logger = SimpleNamespace(
        debug=lambda *args, **kwargs: None, exception=lambda *args, **kwargs: None
    )
    state = _state()
    state.last_high_frequency_check = datetime(2026, 3, 23, 10, 0, 0, tzinfo=UTC)

    _run_high_frequency_scheduler(
        temp_paths,
        state,
        logger,
        datetime(2026, 3, 23, 10, 2, 5, tzinfo=UTC),
    )

    assert [command[-1] for command in launched] == [
        "2026-03-23T10:01:00+00:00",
        "2026-03-23T10:02:00+00:00",
    ]
