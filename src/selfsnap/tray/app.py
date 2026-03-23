from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass
from datetime import UTC, datetime

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.db import connect, ensure_database
from selfsnap.logging_setup import setup_logging
from selfsnap.models import AppConfig, CaptureRecord, OutcomeCategory
from selfsnap.paths import AppPaths, resolve_app_paths
from selfsnap.records import get_latest_record, resolve_latest_capture_path
from selfsnap.reset_service import perform_clean_reset
from selfsnap.retention import apply_retention
from selfsnap.runtime_launch import (
    resolve_manual_capture_background_invocation,
    run_background_command,
)
from selfsnap.runtime_probe import probe_runtime_dependencies
from selfsnap.scheduler.reconcile import reconcile_missed_slots
from selfsnap.scheduler.task_scheduler import sync_scheduler_from_config
from selfsnap.tray.first_run import show_first_run_dialog
from selfsnap.tray.report_issue_window import show_report_issue_dialog
from selfsnap.tray.settings_window import show_settings_dialog
from selfsnap.tray.startup import sync_startup_shortcut
from selfsnap.worker import EXIT_OK


@dataclass(slots=True)
class TrayRuntimeState:
    stop_event: threading.Event
    ui_dialog_open: threading.Event
    last_announced_record_id: str | None = None


def run_tray_app(paths: AppPaths | None = None) -> int:
    probe = probe_runtime_dependencies()
    if not probe.ok:
        print(f"Tray runtime check failed: {probe.summary}")
        print(probe.details)
        return 1

    import pystray
    from PIL import Image, ImageDraw

    paths = paths or resolve_app_paths()
    paths.ensure_dirs()
    config = load_or_create_config(paths)
    ensure_database(paths.db_path)
    logger = setup_logging(paths, config.log_level)

    config = _ensure_first_run_completed(paths, config)
    _sync_startup_shortcut_safe(paths, config, logger)
    sync_scheduler_from_config(paths, emit_console=False)
    _run_housekeeping(paths)

    state = TrayRuntimeState(
        stop_event=threading.Event(),
        ui_dialog_open=threading.Event(),
        last_announced_record_id=_latest_record_id(paths),
    )
    icon = pystray.Icon("selfsnap", _build_icon_image(Image, ImageDraw), "SelfSnap Win11")

    def refresh_menu() -> None:
        icon.menu = pystray.Menu(*_build_menu_items(pystray, paths, icon, state))
        icon.title = _icon_title(paths)
        icon.update_menu()

    def background_loop() -> None:
        while not state.stop_event.is_set():
            try:
                if state.ui_dialog_open.is_set():
                    state.stop_event.wait(60)
                    continue
                _run_housekeeping(paths)
                refresh_menu()
                _announce_latest_record(paths, icon, state)
            except Exception:
                logger.exception("Background maintenance loop failed")
            state.stop_event.wait(60)

    refresh_menu()
    threading.Thread(target=background_loop, daemon=True).start()
    icon.run()
    return EXIT_OK


def _build_icon_image(image_module, draw_module):
    image = image_module.new("RGB", (64, 64), color=(30, 30, 30))
    draw = draw_module.Draw(image)
    draw.rectangle((10, 14, 54, 42), fill=(240, 240, 240))
    draw.rectangle((18, 22, 46, 34), fill=(60, 140, 220))
    draw.rectangle((24, 46, 40, 50), fill=(200, 200, 200))
    return image


def _build_menu_items(pystray, paths: AppPaths, icon, state: TrayRuntimeState) -> list:
    config = load_or_create_config(paths)
    items = []
    warning_label = _scheduler_warning_label(config)
    if warning_label:
        items.append(pystray.MenuItem(warning_label, None, enabled=False))
    items.append(pystray.MenuItem(lambda _item: _state_label(config), None, enabled=False))
    if config.show_last_capture_status:
        items.append(pystray.MenuItem(lambda _item: _latest_label(paths), None, enabled=False))
    items.extend(
        [
            pystray.MenuItem(
                "Report Issue",
                lambda _icon, _item: _run_async(_open_report_issue, paths, icon, state),
                default=True,
            ),
            pystray.MenuItem(
                "Capture Now", lambda _icon, _item: _run_async(_capture_now, paths, icon, state)
            ),
            pystray.MenuItem(
                lambda _item: _toggle_enabled_label(config),
                lambda _icon, _item: _toggle_enabled(paths, icon),
            ),
            pystray.MenuItem(
                "Open Capture Folder", lambda _icon, _item: _open_capture_folder(paths)
            ),
            pystray.MenuItem(
                "Open Latest Capture", lambda _icon, _item: _open_latest_capture(paths)
            ),
            pystray.MenuItem(
                "Settings", lambda _icon, _item: _run_async(_open_settings, paths, icon, state)
            ),
            pystray.MenuItem("Exit", lambda _icon, _item: _exit(icon, state.stop_event)),
        ]
    )
    return items


def _run_async(func, *args) -> None:
    threading.Thread(target=func, args=args, daemon=True).start()


def _capture_now(paths: AppPaths, icon, state: TrayRuntimeState) -> None:
    config = load_or_create_config(paths)
    setup_logging(paths, config.log_level)
    suppress_ui_updates = state.ui_dialog_open.is_set()
    previous_record_id = state.last_announced_record_id
    completed = run_background_command(resolve_manual_capture_background_invocation(paths))
    latest = _latest_record(paths)
    if latest is not None and latest.record_id != previous_record_id:
        if not suppress_ui_updates:
            _announce_record(
                icon,
                config,
                latest,
                suppress_overlay=False,
            )
        state.last_announced_record_id = latest.record_id
    elif completed.returncode != EXIT_OK and not suppress_ui_updates:
        _show_notification(
            icon, "SelfSnap", "Manual capture failed. Open logs or run selfsnap diag."
        )
    if not suppress_ui_updates:
        icon.update_menu()


def _toggle_enabled(paths: AppPaths, icon) -> None:
    config = load_or_create_config(paths)
    if config.app_enabled:
        config.app_enabled = False
    else:
        if not config.first_run_completed:
            updated = show_first_run_dialog(config, paths)
            if updated is None:
                icon.update_menu()
                return
            config = updated
        else:
            config.app_enabled = True
    save_config(paths, config)
    sync_scheduler_from_config(paths, emit_console=False)
    icon.update_menu()


def _open_settings(paths: AppPaths, icon, state: TrayRuntimeState) -> None:
    if state.ui_dialog_open.is_set():
        return
    config = load_or_create_config(paths)
    state.ui_dialog_open.set()
    try:
        result = show_settings_dialog(config, paths)
    finally:
        state.ui_dialog_open.clear()

    if result.requested_reset:
        state.stop_event.set()
        logging.shutdown()
        perform_clean_reset(paths)
        _exit(icon, state.stop_event)
        return
    if result.updated_config is None:
        return
    updated = result.updated_config
    save_config(paths, updated)
    _sync_startup_shortcut_safe(paths, updated, setup_logging(paths, updated.log_level))
    sync_scheduler_from_config(paths, emit_console=False)
    icon.update_menu()


def _open_report_issue(paths: AppPaths, icon, state: TrayRuntimeState) -> None:
    if state.ui_dialog_open.is_set():
        return
    state.ui_dialog_open.set()
    try:
        show_report_issue_dialog(paths)
    finally:
        state.ui_dialog_open.clear()
    icon.update_menu()


def _open_capture_folder(paths: AppPaths) -> None:
    config = load_or_create_config(paths)
    folder = paths.resolve_capture_root(config)
    folder.mkdir(parents=True, exist_ok=True)
    os.startfile(folder)


def _open_latest_capture(paths: AppPaths) -> None:
    ensure_database(paths.db_path)
    with connect(paths.db_path) as connection:
        latest = resolve_latest_capture_path(connection)
    if latest and latest.exists():
        os.startfile(latest)


def _state_label(config: AppConfig) -> str:
    if not config.first_run_completed:
        return "State: setup required"
    if not config.app_enabled:
        return "State: disabled"
    if config.scheduler_sync_failed():
        return "State: enabled, scheduler sync failed"
    return "State: enabled"


def _scheduler_warning_label(config: AppConfig) -> str | None:
    if not config.scheduler_sync_failed():
        return None
    return "Warning: scheduler sync failed - open Settings"


def _latest_label(paths: AppPaths) -> str:
    ensure_database(paths.db_path)
    with connect(paths.db_path) as connection:
        latest = get_latest_record(connection)
    if latest is None:
        return "Latest: none"
    timestamp = latest.created_utc.replace("T", " ").replace("+00:00", "Z")
    return f"Latest: {latest.outcome_code} at {timestamp}"


def _toggle_enabled_label(config: AppConfig) -> str:
    return "Disable Scheduled Captures" if config.app_enabled else "Enable Scheduled Captures"


def _icon_title(paths: AppPaths) -> str:
    config = load_or_create_config(paths)
    if config.scheduler_sync_failed():
        return "SelfSnap Win11 - scheduler sync failed"
    if not config.first_run_completed:
        return "SelfSnap Win11 - setup required"
    return "SelfSnap Win11"


def _exit(icon, stop_event: threading.Event) -> None:
    stop_event.set()
    icon.stop()


def _run_housekeeping(paths: AppPaths) -> None:
    config = load_or_create_config(paths)
    ensure_database(paths.db_path)
    with connect(paths.db_path) as connection:
        apply_retention(connection, config, paths=paths, now_utc=datetime.now(UTC))
    reconcile_missed_slots(paths)


def _ensure_first_run_completed(paths: AppPaths, config: AppConfig) -> AppConfig:
    if config.first_run_completed:
        return config
    updated = show_first_run_dialog(config, paths)
    if updated is None:
        if config.app_enabled:
            config.app_enabled = False
            save_config(paths, config)
        return config
    save_config(paths, updated)
    return updated


def _latest_record_id(paths: AppPaths) -> str | None:
    latest = _latest_record(paths)
    return latest.record_id if latest is not None else None


def _latest_record(paths: AppPaths) -> CaptureRecord | None:
    ensure_database(paths.db_path)
    with connect(paths.db_path) as connection:
        return get_latest_record(connection)


def _announce_latest_record(paths: AppPaths, icon, state: TrayRuntimeState) -> None:
    latest = _latest_record(paths)
    if latest is None or latest.record_id == state.last_announced_record_id:
        return
    config = load_or_create_config(paths)
    _announce_record(
        icon,
        config,
        latest,
        suppress_overlay=state.ui_dialog_open.is_set(),
    )
    state.last_announced_record_id = latest.record_id


def _announce_record(
    icon,
    config: AppConfig,
    record: CaptureRecord,
    suppress_overlay: bool = False,
) -> None:
    if record.outcome_category in {OutcomeCategory.FAILED.value, OutcomeCategory.MISSED.value}:
        if config.notify_on_failed_or_missed:
            _show_notification(icon, "SelfSnap", _format_record_message(record))
        return

    if record.outcome_category == OutcomeCategory.SUCCESS.value:
        if config.notify_on_every_capture:
            _show_notification(icon, "SelfSnap", _format_record_message(record))
        if config.show_capture_overlay and not suppress_overlay:
            _show_capture_overlay()


def _format_record_message(record: CaptureRecord) -> str:
    schedule_suffix = f" ({record.schedule_id})" if record.schedule_id else ""
    return f"{record.outcome_code}{schedule_suffix}"


def _show_notification(icon, title: str, message: str) -> None:
    notify = getattr(icon, "notify", None)
    if notify is None:
        return
    try:
        notify(message, title)
    except Exception:
        return


def _show_capture_overlay() -> None:
    def run_overlay() -> None:
        try:
            import tkinter as tk
        except ImportError:
            return

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.88)
        root.configure(bg="#0f172a")

        width = 280
        height = 72
        screen_width = root.winfo_screenwidth()
        x = int((screen_width - width) / 2)
        y = 40
        root.geometry(f"{width}x{height}+{x}+{y}")

        label = tk.Label(
            root,
            text="SelfSnap captured",
            bg="#0f172a",
            fg="#f8fafc",
            font=("Segoe UI", 14, "bold"),
            padx=18,
            pady=18,
        )
        label.pack(fill="both", expand=True)
        root.after(900, root.destroy)
        root.mainloop()

    threading.Thread(target=run_overlay, daemon=True).start()


def _sync_startup_shortcut_safe(paths: AppPaths, config: AppConfig, logger) -> None:
    try:
        sync_startup_shortcut(paths, config)
    except Exception:
        logger.exception("Failed to sync startup shortcut")
