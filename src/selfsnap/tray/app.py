from __future__ import annotations

from datetime import datetime
import os
import threading

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.db import connect, ensure_database
from selfsnap.logging_setup import setup_logging
from selfsnap.models import DEFAULT_PAUSE_MINUTES, TriggerSource
from selfsnap.paths import AppPaths, resolve_app_paths
from selfsnap.records import get_latest_record, resolve_latest_capture_path
from selfsnap.scheduler.reconcile import reconcile_missed_slots
from selfsnap.scheduler.task_scheduler import sync_scheduler_from_config
from selfsnap.tray.settings_window import show_settings_dialog
from selfsnap.worker import EXIT_OK, run_capture_command


def run_tray_app(paths: AppPaths | None = None) -> int:
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError as exc:
        print(f"Tray dependencies are missing: {exc}")
        return 1

    paths = paths or resolve_app_paths()
    config = load_or_create_config(paths)
    paths.ensure_dirs()
    ensure_database(paths.db_path)
    logger = setup_logging(paths, config.log_level)
    sync_scheduler_from_config(paths)
    reconcile_missed_slots(paths)

    stop_event = threading.Event()
    icon = pystray.Icon("selfsnap", _build_icon_image(Image, ImageDraw), "SelfSnap Win11")

    def refresh_menu() -> None:
        icon.menu = pystray.Menu(
            pystray.MenuItem(lambda _item: _state_label(paths), None, enabled=False),
            pystray.MenuItem(lambda _item: _latest_label(paths), None, enabled=False),
            pystray.MenuItem("Capture Now", lambda _icon, _item: _run_async(_capture_now, paths)),
            pystray.MenuItem(lambda _item: _toggle_enabled_label(paths), lambda _icon, _item: _toggle_enabled(paths, icon)),
            pystray.MenuItem(lambda _item: _pause_label(paths), lambda _icon, _item: _toggle_pause(paths, icon)),
            pystray.MenuItem("Open Capture Folder", lambda _icon, _item: _open_capture_folder(paths)),
            pystray.MenuItem("Open Latest Capture", lambda _icon, _item: _open_latest_capture(paths)),
            pystray.MenuItem("Settings", lambda _icon, _item: _run_async(_open_settings, paths, icon)),
            pystray.MenuItem("Exit", lambda _icon, _item: _exit(icon, stop_event)),
        )
        icon.update_menu()

    def background_loop() -> None:
        while not stop_event.is_set():
            try:
                reconcile_missed_slots(paths)
                refresh_menu()
            except Exception:
                logger.exception("Background reconcile loop failed")
            stop_event.wait(60)

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


def _run_async(func, *args) -> None:
    threading.Thread(target=func, args=args, daemon=True).start()


def _capture_now(paths: AppPaths) -> None:
    config = load_or_create_config(paths)
    setup_logging(paths, config.log_level)
    run_capture_command(TriggerSource.MANUAL, paths=paths)


def _toggle_enabled(paths: AppPaths, icon) -> None:
    config = load_or_create_config(paths)
    config.app_enabled = not config.app_enabled
    save_config(paths, config)
    sync_scheduler_from_config(paths)
    icon.update_menu()


def _toggle_pause(paths: AppPaths, icon) -> None:
    config = load_or_create_config(paths)
    if config.is_paused():
        config.pause_until_local = None
    else:
        config.pause_for_default_duration()
    save_config(paths, config)
    icon.update_menu()


def _open_settings(paths: AppPaths, icon) -> None:
    config = load_or_create_config(paths)
    updated = show_settings_dialog(config)
    if updated is None:
        return
    save_config(paths, updated)
    sync_scheduler_from_config(paths)
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


def _state_label(paths: AppPaths) -> str:
    config = load_or_create_config(paths)
    if not config.app_enabled:
        return "State: disabled"
    if config.is_paused():
        return f"State: paused until {config.pause_until_local}"
    return "State: enabled"


def _latest_label(paths: AppPaths) -> str:
    ensure_database(paths.db_path)
    with connect(paths.db_path) as connection:
        latest = get_latest_record(connection)
    if latest is None:
        return "Latest: none"
    return f"Latest: {latest.outcome_code} at {latest.created_utc}"


def _toggle_enabled_label(paths: AppPaths) -> str:
    config = load_or_create_config(paths)
    return "Disable Scheduled Captures" if config.app_enabled else "Enable Scheduled Captures"


def _pause_label(paths: AppPaths) -> str:
    config = load_or_create_config(paths)
    if config.is_paused():
        return "Resume Now"
    return f"Pause {DEFAULT_PAUSE_MINUTES} Minutes"


def _exit(icon, stop_event: threading.Event) -> None:
    stop_event.set()
    icon.stop()
