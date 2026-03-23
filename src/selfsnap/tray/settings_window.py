from __future__ import annotations

from dataclasses import dataclass, replace
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from selfsnap.models import AppConfig, ConfigValidationError, Schedule, StoragePreset
from selfsnap.paths import AppPaths
from selfsnap.storage import apply_storage_preset, validate_storage_config


WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 760


@dataclass(slots=True)
class SettingsDialogResult:
    updated_config: AppConfig | None
    window_size: tuple[int, int]
    requested_reset: bool = False


def show_settings_dialog(config: AppConfig, paths: AppPaths) -> SettingsDialogResult:
    root = tk.Tk()
    root.title("SelfSnap Settings")
    root.update_idletasks()
    root.geometry(
        f"{max(config.settings_window_width, WINDOW_MIN_WIDTH)}x"
        f"{max(config.settings_window_height, WINDOW_MIN_HEIGHT)}"
    )
    root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
    root.resizable(True, True)

    preset_var = tk.StringVar(value=config.storage_preset)
    capture_root_var = tk.StringVar(value=config.capture_storage_root)
    archive_root_var = tk.StringVar(value=config.archive_storage_root)
    retention_mode_var = tk.StringVar(value=config.retention_mode)
    retention_days_var = tk.StringVar(value="" if config.retention_days is None else str(config.retention_days))
    start_tray_on_login_var = tk.BooleanVar(value=config.start_tray_on_login)
    wake_for_scheduled_captures_var = tk.BooleanVar(value=config.wake_for_scheduled_captures)
    show_last_capture_status_var = tk.BooleanVar(value=config.show_last_capture_status)
    notify_on_failed_or_missed_var = tk.BooleanVar(value=config.notify_on_failed_or_missed)
    notify_on_every_capture_var = tk.BooleanVar(value=config.notify_on_every_capture)
    show_capture_overlay_var = tk.BooleanVar(value=config.show_capture_overlay)
    internal_preset_update = {"active": False}

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    container = ttk.Frame(root, padding=(0, 0, 0, 0))
    container.grid(row=0, column=0, sticky="nsew")
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, weight=1)

    canvas = tk.Canvas(container, highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=scrollbar.set)

    content = ttk.Frame(canvas, padding=16)
    content.columnconfigure(0, weight=1)
    canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")

    def _sync_canvas(_event=None) -> None:
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfigure(canvas_window, width=canvas.winfo_width())

    content.bind("<Configure>", _sync_canvas)
    canvas.bind("<Configure>", _sync_canvas)

    def _bind_wrap(widget: ttk.Label, padding: int = 56) -> None:
        def _update_wrap(_event=None) -> None:
            wrap = max(content.winfo_width() - padding, 420)
            widget.configure(wraplength=wrap)

        content.bind("<Configure>", _update_wrap, add="+")
        root.after_idle(_update_wrap)

    def _stabilize_geometry() -> None:
        root.update_idletasks()
        required_width = max(WINDOW_MIN_WIDTH, root.winfo_reqwidth() + 24)
        required_height = max(WINDOW_MIN_HEIGHT, root.winfo_reqheight() + 24)
        current_width = max(root.winfo_width(), required_width)
        current_height = max(root.winfo_height(), required_height)
        root.minsize(required_width, required_height)
        root.geometry(f"{current_width}x{current_height}")

    def _set_preset(preset: str) -> None:
        internal_preset_update["active"] = True
        try:
            preset_config = apply_storage_preset(paths, config, preset)
            preset_var.set(preset)
            capture_root_var.set(preset_config.capture_storage_root)
            archive_root_var.set(preset_config.archive_storage_root)
        finally:
            internal_preset_update["active"] = False
        _update_path_state()

    def _mark_custom(*_args) -> None:
        if internal_preset_update["active"]:
            return
        if preset_var.get() != StoragePreset.CUSTOM.value:
            preset_var.set(StoragePreset.CUSTOM.value)

    def _update_path_state() -> None:
        capture_entry.configure(state="normal")
        archive_entry.configure(state="normal")
        capture_browse.configure(state="normal")
        archive_browse.configure(state="normal")

    capture_root_var.trace_add("write", _mark_custom)
    archive_root_var.trace_add("write", _mark_custom)

    row = 0
    storage_frame = ttk.LabelFrame(content, text="Storage", padding=12)
    storage_frame.grid(row=row, column=0, sticky="ew")
    storage_frame.columnconfigure(1, weight=1)
    row += 1

    ttk.Label(storage_frame, text="Storage preset").grid(row=0, column=0, sticky="w", pady=(0, 8))
    preset_combo = ttk.Combobox(
        storage_frame,
        textvariable=preset_var,
        state="readonly",
        values=[
            StoragePreset.LOCAL_PICTURES.value,
            StoragePreset.ONEDRIVE_PICTURES.value,
            StoragePreset.CUSTOM.value,
        ],
        width=24,
    )
    preset_combo.grid(row=0, column=1, sticky="w", pady=(0, 8))

    ttk.Label(storage_frame, text="Capture storage root").grid(row=1, column=0, sticky="w", pady=(0, 8))
    capture_entry = ttk.Entry(storage_frame, textvariable=capture_root_var)
    capture_entry.grid(row=1, column=1, sticky="ew", pady=(0, 8))
    capture_browse = ttk.Button(
        storage_frame,
        text="Browse",
        command=lambda: _browse_directory(root, capture_root_var),
    )
    capture_browse.grid(row=1, column=2, sticky="w", padx=(8, 0), pady=(0, 8))

    ttk.Label(storage_frame, text="Archive storage root").grid(row=2, column=0, sticky="w", pady=(0, 8))
    archive_entry = ttk.Entry(storage_frame, textvariable=archive_root_var)
    archive_entry.grid(row=2, column=1, sticky="ew", pady=(0, 8))
    archive_browse = ttk.Button(
        storage_frame,
        text="Browse",
        command=lambda: _browse_directory(root, archive_root_var),
    )
    archive_browse.grid(row=2, column=2, sticky="w", padx=(8, 0), pady=(0, 8))

    ttk.Label(storage_frame, text="Retention mode").grid(row=3, column=0, sticky="w")
    ttk.Combobox(
        storage_frame,
        textvariable=retention_mode_var,
        values=["keep_forever", "keep_days"],
        width=18,
        state="readonly",
    ).grid(row=3, column=1, sticky="w")
    ttk.Label(storage_frame, text="Retention days").grid(row=3, column=2, sticky="w", padx=(12, 0))
    ttk.Entry(storage_frame, textvariable=retention_days_var, width=8).grid(row=3, column=3, sticky="w")

    schedules_frame = ttk.LabelFrame(content, text="Schedules", padding=12)
    schedules_frame.grid(row=row, column=0, sticky="ew", pady=(12, 0))
    schedules_frame.columnconfigure(0, weight=1)
    row += 1

    ttk.Label(
        schedules_frame,
        text="One per line: schedule_id,label,HH:MM,enabled",
    ).grid(row=0, column=0, sticky="w", pady=(0, 8))
    schedules_text = tk.Text(schedules_frame, height=10, wrap="none")
    schedules_text.grid(row=1, column=0, sticky="nsew")
    schedules_text.insert("1.0", _serialize_schedules(config.schedules))

    visibility_frame = ttk.LabelFrame(content, text="Visibility", padding=12)
    visibility_frame.grid(row=row, column=0, sticky="ew", pady=(12, 0))
    visibility_frame.columnconfigure(0, weight=1)
    row += 1

    ttk.Checkbutton(
        visibility_frame,
        text="Start tray on login",
        variable=start_tray_on_login_var,
    ).grid(row=0, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Wake for scheduled captures when supported",
        variable=wake_for_scheduled_captures_var,
    ).grid(row=1, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Show latest capture status in tray menu",
        variable=show_last_capture_status_var,
    ).grid(row=2, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Notify on failed or missed captures",
        variable=notify_on_failed_or_missed_var,
    ).grid(row=3, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Notify on every scheduled and manual capture",
        variable=notify_on_every_capture_var,
    ).grid(row=4, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Show brief on-screen overlay after capture",
        variable=show_capture_overlay_var,
    ).grid(row=5, column=0, sticky="w")

    maintenance_frame = ttk.LabelFrame(content, text="Maintenance", padding=12)
    maintenance_frame.grid(row=row, column=0, sticky="ew", pady=(12, 0))
    maintenance_frame.columnconfigure(0, weight=1)
    row += 1

    maintenance_message = ttk.Label(
        maintenance_frame,
        text=(
            "Reset Capture History permanently deletes SelfSnap capture/archive files, "
            "database history, logs, schedules, and local user settings, then relaunches first run."
        ),
        justify="left",
        foreground="#7f1d1d",
    )
    maintenance_message.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    _bind_wrap(maintenance_message)

    result = SettingsDialogResult(updated_config=None, window_size=(config.settings_window_width, config.settings_window_height))

    def _capture_size() -> tuple[int, int]:
        root.update_idletasks()
        return max(root.winfo_width(), WINDOW_MIN_WIDTH), max(root.winfo_height(), WINDOW_MIN_HEIGHT)

    def _request_reset() -> None:
        confirmed = messagebox.askyesno(
            "Reset Capture History",
            (
                "This permanently deletes SelfSnap capture files, archive files, logs, "
                "history, schedules, and user settings, then restarts into first run.\n\n"
                "This cannot be undone.\n\nContinue?"
            ),
            parent=root,
            icon="warning",
        )
        if not confirmed:
            return
        result.window_size = _capture_size()
        result.requested_reset = True
        root.destroy()

    ttk.Button(
        maintenance_frame,
        text="Reset Capture History",
        command=_request_reset,
    ).grid(row=1, column=0, sticky="w")

    action_row = ttk.Frame(root, padding=(16, 12))
    action_row.grid(row=1, column=0, sticky="ew")

    def _save_and_close() -> None:
        try:
            parsed_schedules = _parse_schedules(schedules_text.get("1.0", "end").strip())
            retention_days = None
            if retention_mode_var.get() == "keep_days":
                retention_days = int(retention_days_var.get())
            updated = replace(
                config,
                storage_preset=preset_var.get().strip(),
                capture_storage_root=capture_root_var.get().strip(),
                archive_storage_root=archive_root_var.get().strip(),
                retention_mode=retention_mode_var.get().strip(),
                retention_days=retention_days,
                start_tray_on_login=start_tray_on_login_var.get(),
                wake_for_scheduled_captures=wake_for_scheduled_captures_var.get(),
                show_last_capture_status=show_last_capture_status_var.get(),
                notify_on_failed_or_missed=notify_on_failed_or_missed_var.get(),
                notify_on_every_capture=notify_on_every_capture_var.get(),
                show_capture_overlay=show_capture_overlay_var.get(),
                settings_window_width=_capture_size()[0],
                settings_window_height=_capture_size()[1],
                schedules=parsed_schedules,
            )
            if updated.storage_preset != StoragePreset.CUSTOM.value:
                updated = apply_storage_preset(paths, updated, updated.storage_preset)
            else:
                validate_storage_config(paths, updated)
            updated.validate()
        except (ConfigValidationError, ValueError) as exc:
            messagebox.showerror("Invalid settings", str(exc), parent=root)
            return
        result.updated_config = updated
        result.window_size = _capture_size()
        root.destroy()

    def _cancel() -> None:
        result.window_size = _capture_size()
        root.destroy()

    ttk.Button(action_row, text="Save", command=_save_and_close).pack(side="right")
    ttk.Button(action_row, text="Cancel", command=_cancel).pack(side="right", padx=(0, 8))

    preset_combo.bind("<<ComboboxSelected>>", lambda _event: _set_preset(preset_var.get()))
    _update_path_state()
    root.after_idle(_stabilize_geometry)
    root.protocol("WM_DELETE_WINDOW", _cancel)
    root.mainloop()
    return result


def _browse_directory(parent: tk.Tk, target: tk.StringVar) -> None:
    chosen = filedialog.askdirectory(parent=parent, initialdir=target.get() or None)
    if chosen:
        target.set(chosen)


def _serialize_schedules(schedules: list[Schedule]) -> str:
    return "\n".join(
        f"{schedule.schedule_id},{schedule.label},{schedule.local_time},{str(schedule.enabled).lower()}"
        for schedule in schedules
    )


def _parse_schedules(raw_text: str) -> list[Schedule]:
    schedules: list[Schedule] = []
    if not raw_text.strip():
        return schedules
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) not in {3, 4}:
            raise ConfigValidationError(
                "Each schedule line must be schedule_id,label,HH:MM or schedule_id,label,HH:MM,enabled"
            )
        enabled = True
        if len(parts) == 4:
            enabled = parts[3].lower() not in {"false", "0", "no"}
        schedule = Schedule(schedule_id=parts[0], label=parts[1], local_time=parts[2], enabled=enabled)
        schedule.validate()
        schedules.append(schedule)
    return schedules
