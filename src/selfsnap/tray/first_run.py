from __future__ import annotations

from dataclasses import replace
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from selfsnap.models import AppConfig, ConfigValidationError
from selfsnap.paths import AppPaths


def show_first_run_dialog(config: AppConfig, paths: AppPaths) -> AppConfig | None:
    root = tk.Tk()
    root.title("SelfSnap First Run Setup")
    root.geometry("680x420")
    root.resizable(False, False)

    capture_root_var = tk.StringVar(value=config.capture_storage_root or str(paths.default_capture_root))
    archive_root_var = tk.StringVar(value=config.archive_storage_root or str(paths.default_archive_root))
    enable_schedules_var = tk.BooleanVar(value=config.app_enabled)
    show_last_capture_status_var = tk.BooleanVar(value=config.show_last_capture_status)
    notify_on_failed_or_missed_var = tk.BooleanVar(value=config.notify_on_failed_or_missed)
    notify_on_every_capture_var = tk.BooleanVar(value=config.notify_on_every_capture)
    show_capture_overlay_var = tk.BooleanVar(value=config.show_capture_overlay)

    ttk.Label(
        root,
        text=(
            "SelfSnap stores screenshots locally and can start scheduled capture after setup. "
            "Manual capture remains available even if you leave scheduling off."
        ),
        wraplength=640,
        justify="left",
    ).pack(anchor="w", padx=12, pady=(12, 8))

    ttk.Label(root, text="Capture storage root").pack(anchor="w", padx=12)
    capture_row = tk.Frame(root)
    capture_row.pack(fill="x", padx=12)
    ttk.Entry(capture_row, textvariable=capture_root_var, width=62).pack(side="left", fill="x", expand=True)
    ttk.Button(capture_row, text="Browse", command=lambda: _browse_directory(capture_root_var)).pack(
        side="left", padx=(8, 0)
    )

    ttk.Label(root, text="Archive storage root").pack(anchor="w", padx=12, pady=(12, 0))
    archive_row = tk.Frame(root)
    archive_row.pack(fill="x", padx=12)
    ttk.Entry(archive_row, textvariable=archive_root_var, width=62).pack(side="left", fill="x", expand=True)
    ttk.Button(archive_row, text="Browse", command=lambda: _browse_directory(archive_root_var)).pack(
        side="left", padx=(8, 0)
    )

    options_frame = tk.LabelFrame(root, text="Visibility defaults")
    options_frame.pack(fill="x", padx=12, pady=(12, 0))
    tk.Checkbutton(
        options_frame,
        text="Show latest capture status in tray menu",
        variable=show_last_capture_status_var,
    ).pack(anchor="w", padx=12, pady=(8, 0))
    tk.Checkbutton(
        options_frame,
        text="Notify on failed or missed captures",
        variable=notify_on_failed_or_missed_var,
    ).pack(anchor="w", padx=12)
    tk.Checkbutton(
        options_frame,
        text="Notify on every scheduled and manual capture",
        variable=notify_on_every_capture_var,
    ).pack(anchor="w", padx=12)
    tk.Checkbutton(
        options_frame,
        text="Show brief on-screen overlay after capture",
        variable=show_capture_overlay_var,
    ).pack(anchor="w", padx=12, pady=(0, 8))

    tk.Checkbutton(
        root,
        text="Enable scheduled capture after setup",
        variable=enable_schedules_var,
    ).pack(anchor="w", padx=12, pady=(12, 0))

    result: dict[str, AppConfig | None] = {"value": None}

    def save_and_close() -> None:
        try:
            updated = replace(
                config,
                first_run_completed=True,
                app_enabled=enable_schedules_var.get(),
                capture_storage_root=capture_root_var.get().strip(),
                archive_storage_root=archive_root_var.get().strip(),
                show_last_capture_status=show_last_capture_status_var.get(),
                notify_on_failed_or_missed=notify_on_failed_or_missed_var.get(),
                notify_on_every_capture=notify_on_every_capture_var.get(),
                show_capture_overlay=show_capture_overlay_var.get(),
            )
            updated.validate()
        except ConfigValidationError as exc:
            messagebox.showerror("Invalid setup", str(exc), parent=root)
            return
        result["value"] = updated
        root.destroy()

    button_row = tk.Frame(root)
    button_row.pack(fill="x", padx=12, pady=(12, 12))
    ttk.Button(button_row, text="Finish Setup", command=save_and_close).pack(side="right")
    ttk.Button(button_row, text="Cancel", command=root.destroy).pack(side="right", padx=(0, 8))

    root.mainloop()
    return result["value"]


def _browse_directory(target: tk.StringVar) -> None:
    chosen = filedialog.askdirectory(initialdir=target.get() or None)
    if chosen:
        target.set(chosen)
