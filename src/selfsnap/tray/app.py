from __future__ import annotations

import ctypes
import logging
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import tkinter as tk
from tkinter import messagebox

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.db import connect, ensure_database
from selfsnap.lifecycle_actions import (
    resolve_reinstall_invocation,
    schedule_tray_relaunch_after_exit,
    resolve_uninstall_invocation,
    run_lifecycle_script_and_check,
)
from selfsnap.logging_setup import setup_logging
from selfsnap.models import AppConfig, CaptureRecord, OutcomeCategory
from selfsnap.paths import AppPaths, resolve_app_paths
from selfsnap.recurrence import is_high_frequency_schedule, iter_occurrences_between
from selfsnap.records import get_latest_record, resolve_latest_capture_path
from selfsnap.reset_service import perform_clean_reset
from selfsnap.retention import apply_retention
from selfsnap.runtime_launch import (
    launch_background,
    resolve_manual_capture_background_invocation,
    resolve_worker_background_invocation,
    run_background_command,
)
from selfsnap.runtime_probe import probe_runtime_dependencies
from selfsnap.scheduler.reconcile import reconcile_missed_slots
from selfsnap.scheduler.task_scheduler import sync_scheduler_from_config
from selfsnap.tray.first_run import show_first_run_dialog
from selfsnap.tray.recent_captures_window import show_recent_captures_window
from selfsnap.tray.report_issue_window import show_report_issue_dialog
from selfsnap.tray.settings_window import show_settings_dialog
from selfsnap.tray.startup import sync_startup_shortcut
from selfsnap.tray.statistics_window import show_statistics_window
from selfsnap.ui.fluent import ACCENT_COLOR, CARD_BG, TEXT_MUTED, TEXT_PRIMARY
from selfsnap.ui.presentation import (
    application_title,
    latest_capture_label,
    record_message,
    tray_icon_title,
    tray_state_label,
    tray_status_summary_label,
    tray_toggle_enabled_label,
    tray_warning_label,
)
from selfsnap.worker import EXIT_OK


@dataclass(slots=True)
class TrayRuntimeState:
    stop_event: threading.Event
    settings_dialog_open: threading.Event
    report_dialog_open: threading.Event
    last_high_frequency_check: datetime
    next_housekeeping_at: datetime
    dialog_state_lock: threading.Lock = field(default_factory=threading.Lock)
    last_announced_record_id: str | None = None


_TRAY_MUTEX_NAME = "Local\\SelfSnap_TrayInstance"


def _acquire_tray_mutex() -> int | None:
    """Try to create a named Windows mutex for single-instance enforcement.

    Returns the raw handle to keep alive, or None if another tray is already
    running (ERROR_ALREADY_EXISTS == 183).
    """
    handle = ctypes.windll.kernel32.CreateMutexW(None, True, _TRAY_MUTEX_NAME)  # type: ignore[attr-defined]
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS  # type: ignore[attr-defined]
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]
        return None
    return handle


def run_tray_app(paths: AppPaths | None = None) -> int:
    _mutex_handle = _acquire_tray_mutex()
    if _mutex_handle is None:
        print("SelfSnap tray is already running.")
        return 1

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

    initial_now = datetime.now().astimezone()
    state = TrayRuntimeState(
        stop_event=threading.Event(),
        settings_dialog_open=threading.Event(),
        report_dialog_open=threading.Event(),
        last_high_frequency_check=initial_now - timedelta(seconds=1),
        next_housekeeping_at=initial_now + timedelta(seconds=60),
        last_announced_record_id=_latest_record_id(paths),
    )
    icon = pystray.Icon("selfsnap", _build_icon_image(Image, ImageDraw), application_title())

    def refresh_menu() -> None:
        icon.menu = pystray.Menu(*_build_menu_items(pystray, paths, icon, state, refresh_menu))
        icon.title = _icon_title(paths)
        icon.update_menu()

    def background_loop() -> None:
        while not state.stop_event.is_set():
            try:
                now_local = datetime.now().astimezone()
                _run_high_frequency_scheduler(paths, state, logger, now_local)
                if _announce_latest_record(paths, icon, state):
                    refresh_menu()
                if now_local >= state.next_housekeeping_at:
                    _run_housekeeping(paths)
                    refresh_menu()
                    state.next_housekeeping_at = now_local + timedelta(seconds=60)
            except Exception:
                logger.exception("Background maintenance loop failed")
            state.stop_event.wait(1)

    refresh_menu()
    threading.Thread(target=background_loop, daemon=True).start()
    icon.run()
    return EXIT_OK


def _build_icon_image(image_module, draw_module):
    image = image_module.new("RGB", (64, 64), color=(243, 246, 251))
    draw = draw_module.Draw(image)
    draw.rounded_rectangle((8, 10, 56, 44), radius=10, fill=(255, 255, 255), outline=(216, 225, 236))
    draw.rounded_rectangle((16, 18, 48, 32), radius=6, fill=(11, 92, 171))
    draw.rounded_rectangle((18, 35, 46, 39), radius=2, fill=(234, 243, 255))
    draw.rounded_rectangle((24, 48, 40, 52), radius=2, fill=(100, 116, 139))
    return image


def _build_menu_items(
    pystray,
    paths: AppPaths,
    icon,
    state: TrayRuntimeState,
    refresh_menu: Callable[[], None] | None = None,
) -> list:
    config = load_or_create_config(paths)
    items = []
    warning_label = _scheduler_warning_label(config)
    if warning_label:
        items.append(pystray.MenuItem(warning_label, None, enabled=False))
    items.append(
        pystray.MenuItem(
            lambda _item: _status_summary_label(paths, config),
            None,
            enabled=False,
        )
    )
    items.extend(
        [
            pystray.MenuItem(
                "Capture Now",
                lambda _icon, _item: _run_async(
                    _capture_now, paths, icon, state, refresh_menu
                ),
            ),
            pystray.MenuItem(
                lambda _item: _toggle_enabled_label(config),
                lambda _icon, _item: _toggle_enabled(paths, icon, refresh_menu),
            ),
            pystray.MenuItem(
                "Settings",
                lambda _icon, _item: _run_async(
                    _open_settings, paths, icon, state, refresh_menu
                ),
                default=True,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Browse",
                pystray.Menu(
                    pystray.MenuItem(
                        "Open Last Capture",
                        lambda _icon, _item: _open_latest_capture(paths),
                    ),
                    pystray.MenuItem(
                        "Open Capture Folder",
                        lambda _icon, _item: _open_capture_folder(paths),
                    ),
                    pystray.MenuItem(
                        "Recent Captures",
                        lambda _icon, _item: _run_async(show_recent_captures_window, paths),
                    ),
                    pystray.MenuItem(
                        "Statistics",
                        lambda _icon, _item: _run_async(show_statistics_window, paths),
                    ),
                ),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "App",
                pystray.Menu(
                    pystray.MenuItem(
                        "Check for Updates",
                        lambda _icon, _item: _run_async(
                            _check_for_updates, paths, icon, state
                        ),
                    ),
                    pystray.MenuItem(
                        "Report Issue",
                        lambda _icon, _item: _run_async(
                            _open_report_issue, paths, icon, state, refresh_menu
                        ),
                    ),
                    pystray.MenuItem(
                        "Repair or Reinstall",
                        lambda _icon, _item: _run_async(
                            _reinstall_selfsnap, paths, icon, state, False
                        ),
                    ),
                    pystray.MenuItem(
                        "Restart",
                        lambda _icon, _item: _run_async(_restart_selfsnap, paths, icon, state),
                    ),
                    pystray.MenuItem(
                        "Uninstall",
                        pystray.Menu(
                            pystray.MenuItem(
                                "Keep User Data",
                                lambda _icon, _item: _run_async(
                                    _uninstall_selfsnap, paths, icon, state, False
                                ),
                            ),
                            pystray.MenuItem(
                                "Remove All User Data",
                                lambda _icon, _item: _run_async(
                                    _uninstall_selfsnap, paths, icon, state, True
                                ),
                            ),
                        ),
                    ),
                    pystray.MenuItem(
                        "Exit",
                        lambda _icon, _item: _exit(icon, state.stop_event),
                    ),
                ),
            ),
        ]
    )
    return items


def _run_async(func, *args) -> None:
    threading.Thread(target=func, args=args, daemon=True).start()


def _capture_now(
    paths: AppPaths,
    icon,
    state: TrayRuntimeState,
    refresh_menu: Callable[[], None] | None = None,
) -> None:
    config = load_or_create_config(paths)
    setup_logging(paths, config.log_level)
    suppress_ui_updates = _any_dialog_open(state)
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
        if refresh_menu is not None:
            refresh_menu()
        else:
            icon.update_menu()


def _toggle_enabled(
    paths: AppPaths,
    icon,
    refresh_menu: Callable[[], None] | None = None,
) -> None:
    config = load_or_create_config(paths)
    if config.app_enabled:
        config.app_enabled = False
    else:
        if not config.first_run_completed:
            updated = show_first_run_dialog(config, paths)
            if updated is None:
                if refresh_menu is not None:
                    refresh_menu()
                else:
                    icon.update_menu()
                return
            config = updated
        else:
            config.app_enabled = True
    save_config(paths, config)
    sync_scheduler_from_config(paths, emit_console=False)
    if refresh_menu is not None:
        refresh_menu()
    else:
        icon.update_menu()


def _open_settings(
    paths: AppPaths,
    icon,
    state: TrayRuntimeState,
    refresh_menu: Callable[[], None] | None = None,
) -> None:
    if not _begin_dialog(state, state.settings_dialog_open):
        return
    config = load_or_create_config(paths)
    try:
        result = show_settings_dialog(config, paths)
    finally:
        _end_dialog(state, state.settings_dialog_open)

    if result.requested_reset:
        state.stop_event.set()
        logging.shutdown()
        perform_clean_reset(paths)
        _exit(icon, state.stop_event)
        return
    if result.updated_config is None:
        return
    updated = result.updated_config
    # Config was already written to disk by the settings dialog; apply side-effects only.
    _sync_startup_shortcut_safe(paths, updated, setup_logging(paths, updated.log_level))
    sync_scheduler_from_config(paths, emit_console=False)
    if refresh_menu is not None:
        refresh_menu()
    else:
        icon.update_menu()


def _open_report_issue(
    paths: AppPaths,
    icon,
    state: TrayRuntimeState,
    refresh_menu: Callable[[], None] | None = None,
) -> None:
    if not _begin_dialog(state, state.report_dialog_open):
        return
    try:
        show_report_issue_dialog(paths)
    finally:
        _end_dialog(state, state.report_dialog_open)
    if refresh_menu is not None:
        refresh_menu()
    else:
        icon.update_menu()


def _restart_selfsnap(paths: AppPaths, icon, state: TrayRuntimeState) -> None:
    launched = schedule_tray_relaunch_after_exit(paths, wait_for_process_id=os.getpid())
    if not launched:
        _show_error_dialog(
            "Restart SelfSnap",
            "SelfSnap could not start a replacement tray process. The current tray is still running.",
        )
        return
    _exit(icon, state.stop_event)


def _reinstall_selfsnap(paths: AppPaths, icon, state: TrayRuntimeState, update_source: bool) -> None:
    title = "Reinstall SelfSnap"
    message = (
        "SelfSnap will reinstall itself from the current local source checkout, preserve your "
        "data, and relaunch the tray.\n\nContinue?"
    )
    if not _ask_confirmation(title, message, warning=False):
        return

    succeeded = run_lifecycle_script_and_check(
        resolve_reinstall_invocation(paths, update_source=update_source, relaunch_tray=False)
    )
    if not succeeded:
        _show_error_dialog(
            title,
            "SelfSnap reinstall failed. Check the reinstall.ps1 script output for details.",
        )
        return
    if not schedule_tray_relaunch_after_exit(paths, wait_for_process_id=os.getpid()):
        _show_error_dialog(
            title,
            "SelfSnap reinstalled successfully, but the replacement tray could not be scheduled.",
        )
        return
    _exit(icon, state.stop_event)


def _check_for_updates(paths: AppPaths, icon, state: TrayRuntimeState) -> None:
    from selfsnap.update_checker import compare_versions, fetch_latest_release_tag
    from selfsnap.version import __version__

    title = "Check for Updates"

    latest_tag = fetch_latest_release_tag("Daniel-Lomazov/SelfSnap")
    if latest_tag is None:
        _show_error_dialog(
            title,
            "Could not reach GitHub to check for updates.\n\n"
            "Verify your internet connection and try again.",
        )
        return

    comparison = compare_versions(__version__, latest_tag)
    if comparison >= 0:
        effective_latest = f"v{__version__}" if comparison > 0 else latest_tag
        _show_info_dialog(
            title,
            f"SelfSnap is up to date.\n\nInstalled: v{__version__}\nLatest:    {effective_latest}",
        )
        return

    message = (
        f"A new version is available!\n\n"
        f"  Installed: v{__version__}\n"
        f"  Latest:    {latest_tag}\n\n"
        "Update now? SelfSnap will fetch the new version, reinstall, and relaunch."
    )
    if not _ask_confirmation(title, message, warning=False):
        return

    succeeded = run_lifecycle_script_and_check(
        resolve_reinstall_invocation(
            paths, update_source=True, target_tag=latest_tag, relaunch_tray=False
        )
    )
    if not succeeded:
        _show_error_dialog(
            title,
            f"Update to {latest_tag} failed.\n\n"
            "Check that you have network access and the release tag exists on GitHub.",
        )
        return
    if not schedule_tray_relaunch_after_exit(paths, wait_for_process_id=os.getpid()):
        _show_error_dialog(
            title,
            "Update installed, but the replacement tray could not be scheduled.",
        )
        return
    _exit(icon, state.stop_event)


def _uninstall_selfsnap(
    paths: AppPaths,
    icon,
    state: TrayRuntimeState,
    remove_user_data: bool,
) -> None:
    title = "Uninstall SelfSnap"
    if remove_user_data:
        message = (
            "This removes SelfSnap startup/task/install links and all SelfSnap user data, including "
            "config, database, logs, captures, archive files, and app temp data.\n\n"
            "The source checkout and .venv will stay in place.\n\nContinue?"
        )
    else:
        message = (
            "This removes SelfSnap startup/task/install links but keeps your config, history, logs, "
            "captures, and archive files.\n\nContinue?"
        )
    if not _ask_confirmation(title, message, warning=remove_user_data):
        return

    succeeded = run_lifecycle_script_and_check(
        resolve_uninstall_invocation(paths, remove_user_data=remove_user_data)
    )
    if not succeeded:
        _show_error_dialog(
            title,
            "SelfSnap uninstall failed. The current tray is still running.",
        )
        return
    _exit(icon, state.stop_event)


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
    return tray_state_label(config)


def _scheduler_warning_label(config: AppConfig) -> str | None:
    return tray_warning_label(config)


def _latest_label(paths: AppPaths) -> str:
    ensure_database(paths.db_path)
    with connect(paths.db_path) as connection:
        latest = get_latest_record(connection)
    if latest is None:
        return "Last capture: none yet"
    timestamp_utc = latest.started_utc or latest.created_utc
    timestamp_local = _format_local_timestamp(timestamp_utc)
    return latest_capture_label(latest.outcome_code, timestamp_local)


def _status_summary_label(paths: AppPaths, config: AppConfig) -> str:
    latest_label = _latest_label(paths) if config.show_last_capture_status else None
    return tray_status_summary_label(_state_label(config), latest_label)


def _format_local_timestamp(utc_text: str) -> str:
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


def _toggle_enabled_label(config: AppConfig) -> str:
    return tray_toggle_enabled_label(config.app_enabled)


def _icon_title(paths: AppPaths) -> str:
    config = load_or_create_config(paths)
    return tray_icon_title(config)


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


def _announce_latest_record(paths: AppPaths, icon, state: TrayRuntimeState) -> bool:
    latest = _latest_record(paths)
    if latest is None or latest.record_id == state.last_announced_record_id:
        return False
    config = load_or_create_config(paths)
    _announce_record(
        icon,
        config,
        latest,
        suppress_overlay=_any_dialog_open(state),
        suppress_notifications=_any_dialog_open(state),
    )
    state.last_announced_record_id = latest.record_id
    return True


def _announce_record(
    icon,
    config: AppConfig,
    record: CaptureRecord,
    suppress_overlay: bool = False,
    suppress_notifications: bool = False,
) -> None:
    if record.outcome_category in {OutcomeCategory.FAILED.value, OutcomeCategory.MISSED.value}:
        if config.notify_on_failed_or_missed and not suppress_notifications:
            _show_notification(icon, "SelfSnap", _format_record_message(record))
        return

    if record.outcome_category == OutcomeCategory.SUCCESS.value:
        if config.notify_on_every_capture and not suppress_notifications:
            _show_notification(icon, "SelfSnap", _format_record_message(record))
        if config.show_capture_overlay and not suppress_overlay:
            _show_capture_overlay()


def _format_record_message(record: CaptureRecord) -> str:
    return record_message(record.outcome_code, record.schedule_id)


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
        root.attributes("-alpha", 0.96)
        root.configure(bg=CARD_BG)

        width = 320
        height = 88
        screen_width = root.winfo_screenwidth()
        x = int((screen_width - width) / 2)
        y = 40
        root.geometry(f"{width}x{height}+{x}+{y}")

        accent = tk.Frame(root, bg=ACCENT_COLOR, width=6)
        accent.pack(side="left", fill="y")

        content = tk.Frame(root, bg=CARD_BG, padx=18, pady=14)
        content.pack(side="left", fill="both", expand=True)

        title = tk.Label(
            content,
            text="Capture saved",
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            font=("Segoe UI Semibold", 13),
            anchor="w",
        )
        title.pack(fill="x")

        subtitle = tk.Label(
            content,
            text="SelfSnap wrote a new local screenshot.",
            bg=CARD_BG,
            fg=TEXT_MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        )
        subtitle.pack(fill="x", pady=(4, 0))

        root.after(1100, root.destroy)
        root.mainloop()

    threading.Thread(target=run_overlay, daemon=True).start()


def _sync_startup_shortcut_safe(paths: AppPaths, config: AppConfig, logger) -> None:
    try:
        sync_startup_shortcut(paths, config)
    except Exception:
        logger.exception("Failed to sync startup shortcut")


def _run_high_frequency_scheduler(
    paths: AppPaths,
    state: TrayRuntimeState,
    logger: logging.Logger,
    now_local: datetime,
) -> None:
    previous_check = state.last_high_frequency_check
    if now_local <= previous_check:
        return

    config = load_or_create_config(paths)
    state.last_high_frequency_check = now_local
    if not config.first_run_completed or not config.app_enabled:
        return

    for schedule in config.schedules:
        if not schedule.enabled or not is_high_frequency_schedule(schedule):
            continue
        for planned in iter_occurrences_between(
            schedule,
            previous_check,
            now_local,
            include_start=False,
        ):
            try:
                launch_background(
                    resolve_worker_background_invocation(
                        paths,
                        schedule.schedule_id,
                        planned.isoformat(),
                    )
                )
            except Exception:
                logger.exception(
                    "High-frequency scheduled capture launch failed for %s at %s",
                    schedule.schedule_id,
                    planned.isoformat(),
                )
            else:
                logger.debug(
                    "Launched high-frequency scheduled capture for %s at %s",
                    schedule.schedule_id,
                    planned.isoformat(),
                )


def _any_dialog_open(state: TrayRuntimeState) -> bool:
    return state.settings_dialog_open.is_set() or state.report_dialog_open.is_set()


def _ask_confirmation(title: str, message: str, *, warning: bool) -> bool:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return bool(
            messagebox.askyesno(
                title,
                message,
                parent=root,
                icon="warning" if warning else "question",
            )
        )
    finally:
        root.destroy()


def _show_error_dialog(title: str, message: str) -> None:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        messagebox.showerror(title, message, parent=root)
    finally:
        root.destroy()


def _show_info_dialog(title: str, message: str) -> None:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        messagebox.showinfo(title, message, parent=root)
    finally:
        root.destroy()


def _begin_dialog(state: TrayRuntimeState, dialog_event: threading.Event) -> bool:
    with state.dialog_state_lock:
        if dialog_event.is_set():
            return False
        dialog_event.set()
        return True


def _end_dialog(state: TrayRuntimeState, dialog_event: threading.Event) -> None:
    with state.dialog_state_lock:
        dialog_event.clear()
