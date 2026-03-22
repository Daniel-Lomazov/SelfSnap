from __future__ import annotations

from dataclasses import replace
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from selfsnap.models import AppConfig, ConfigValidationError, StoragePreset
from selfsnap.paths import AppPaths
from selfsnap.storage import apply_storage_preset, validate_storage_config


def show_first_run_dialog(config: AppConfig, paths: AppPaths) -> AppConfig | None:
    root = tk.Tk()
    root.title("SelfSnap First Run Setup")
    root.geometry(f"{max(config.settings_window_width, 720)}x{max(config.settings_window_height, 560)}")
    root.minsize(720, 560)
    root.resizable(True, True)

    preset_var = tk.StringVar(value=config.storage_preset)
    capture_root_var = tk.StringVar(value=config.capture_storage_root or str(paths.default_capture_root))
    archive_root_var = tk.StringVar(value=config.archive_storage_root or str(paths.default_archive_root))
    enable_schedules_var = tk.BooleanVar(value=config.app_enabled)
    show_last_capture_status_var = tk.BooleanVar(value=config.show_last_capture_status)
    notify_on_failed_or_missed_var = tk.BooleanVar(value=config.notify_on_failed_or_missed)
    notify_on_every_capture_var = tk.BooleanVar(value=config.notify_on_every_capture)
    show_capture_overlay_var = tk.BooleanVar(value=config.show_capture_overlay)
    start_tray_on_login_var = tk.BooleanVar(value=config.start_tray_on_login)
    internal_preset_update = {"active": False}

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    content = ttk.Frame(root, padding=16)
    content.grid(row=0, column=0, sticky="nsew")
    content.columnconfigure(0, weight=1)

    ttk.Label(
        content,
        text=(
            "SelfSnap stores screenshots locally and can start scheduled capture after setup. "
            "Manual capture remains available even if you leave scheduling off."
        ),
        wraplength=700,
        justify="left",
    ).grid(row=0, column=0, sticky="w", pady=(0, 12))

    storage_frame = ttk.LabelFrame(content, text="Storage", padding=12)
    storage_frame.grid(row=1, column=0, sticky="ew")
    storage_frame.columnconfigure(1, weight=1)

    def _apply_preset(preset: str) -> None:
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

    visibility_frame = ttk.LabelFrame(content, text="Visibility", padding=12)
    visibility_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
    ttk.Checkbutton(
        visibility_frame,
        text="Start tray on login after setup",
        variable=start_tray_on_login_var,
    ).grid(row=0, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Show latest capture status in tray menu",
        variable=show_last_capture_status_var,
    ).grid(row=1, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Notify on failed or missed captures",
        variable=notify_on_failed_or_missed_var,
    ).grid(row=2, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Notify on every scheduled and manual capture",
        variable=notify_on_every_capture_var,
    ).grid(row=3, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Show brief on-screen overlay after capture",
        variable=show_capture_overlay_var,
    ).grid(row=4, column=0, sticky="w")

    ttk.Checkbutton(
        content,
        text="Enable scheduled capture after setup",
        variable=enable_schedules_var,
    ).grid(row=3, column=0, sticky="w", pady=(12, 0))

    result: dict[str, AppConfig | None] = {"value": None}

    def _save_and_close() -> None:
        try:
            updated = replace(
                config,
                first_run_completed=True,
                app_enabled=enable_schedules_var.get(),
                storage_preset=preset_var.get().strip(),
                capture_storage_root=capture_root_var.get().strip(),
                archive_storage_root=archive_root_var.get().strip(),
                start_tray_on_login=start_tray_on_login_var.get(),
                show_last_capture_status=show_last_capture_status_var.get(),
                notify_on_failed_or_missed=notify_on_failed_or_missed_var.get(),
                notify_on_every_capture=notify_on_every_capture_var.get(),
                show_capture_overlay=show_capture_overlay_var.get(),
                settings_window_width=root.winfo_width(),
                settings_window_height=root.winfo_height(),
            )
            if updated.storage_preset != StoragePreset.CUSTOM.value:
                updated = apply_storage_preset(paths, updated, updated.storage_preset)
            else:
                validate_storage_config(paths, updated)
            updated.validate()
        except ConfigValidationError as exc:
            messagebox.showerror("Invalid setup", str(exc), parent=root)
            return
        result["value"] = updated
        root.destroy()

    button_row = ttk.Frame(content)
    button_row.grid(row=4, column=0, sticky="ew", pady=(16, 0))
    ttk.Button(button_row, text="Finish Setup", command=_save_and_close).pack(side="right")
    ttk.Button(button_row, text="Cancel", command=root.destroy).pack(side="right", padx=(0, 8))

    preset_combo.bind("<<ComboboxSelected>>", lambda _event: _apply_preset(preset_var.get()))
    _update_path_state()
    root.mainloop()
    return result["value"]


def _browse_directory(parent: tk.Tk, target: tk.StringVar) -> None:
    chosen = filedialog.askdirectory(parent=parent, initialdir=target.get() or None)
    if chosen:
        target.set(chosen)
