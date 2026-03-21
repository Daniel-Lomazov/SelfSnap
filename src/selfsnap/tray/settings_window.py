from __future__ import annotations

from dataclasses import replace
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from selfsnap.models import AppConfig, ConfigValidationError, Schedule


def show_settings_dialog(config: AppConfig) -> AppConfig | None:
    root = tk.Tk()
    root.title("SelfSnap Settings")
    root.geometry("640x420")
    root.resizable(False, False)

    capture_root_var = tk.StringVar(value=config.capture_storage_root)
    retention_mode_var = tk.StringVar(value=config.retention_mode)
    retention_days_var = tk.StringVar(value="" if config.retention_days is None else str(config.retention_days))
    schedules_text = tk.Text(root, width=70, height=12)
    schedules_text.insert("1.0", _serialize_schedules(config.schedules))

    tk.Label(root, text="Capture storage root").pack(anchor="w", padx=12, pady=(12, 0))
    storage_row = tk.Frame(root)
    storage_row.pack(fill="x", padx=12)
    tk.Entry(storage_row, textvariable=capture_root_var, width=60).pack(side="left", fill="x", expand=True)
    ttk.Button(storage_row, text="Browse", command=lambda: _browse_directory(capture_root_var)).pack(side="left", padx=(8, 0))

    retention_row = tk.Frame(root)
    retention_row.pack(fill="x", padx=12, pady=(12, 0))
    tk.Label(retention_row, text="Retention mode").pack(side="left")
    ttk.Combobox(
        retention_row,
        textvariable=retention_mode_var,
        values=["keep_forever", "keep_days"],
        width=18,
        state="readonly",
    ).pack(side="left", padx=(8, 16))
    tk.Label(retention_row, text="Retention days").pack(side="left")
    tk.Entry(retention_row, textvariable=retention_days_var, width=8).pack(side="left", padx=(8, 0))

    tk.Label(
        root,
        text="Schedules: one per line in the format schedule_id,label,HH:MM,enabled",
    ).pack(anchor="w", padx=12, pady=(12, 0))
    schedules_text.pack(fill="both", padx=12, pady=(0, 12))

    result: dict[str, AppConfig | None] = {"value": None}

    def save_and_close() -> None:
        try:
            parsed_schedules = _parse_schedules(schedules_text.get("1.0", "end").strip())
            retention_days = None
            if retention_mode_var.get() == "keep_days":
                retention_days = int(retention_days_var.get())
            updated = replace(
                config,
                capture_storage_root=capture_root_var.get().strip(),
                retention_mode=retention_mode_var.get().strip(),
                retention_days=retention_days,
                schedules=parsed_schedules,
            )
            updated.validate()
        except (ConfigValidationError, ValueError) as exc:
            messagebox.showerror("Invalid settings", str(exc), parent=root)
            return
        result["value"] = updated
        root.destroy()

    button_row = tk.Frame(root)
    button_row.pack(fill="x", padx=12, pady=(0, 12))
    ttk.Button(button_row, text="Save", command=save_and_close).pack(side="right")
    ttk.Button(button_row, text="Cancel", command=root.destroy).pack(side="right", padx=(0, 8))

    root.mainloop()
    return result["value"]


def _browse_directory(target: tk.StringVar) -> None:
    chosen = filedialog.askdirectory(initialdir=target.get() or None)
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

