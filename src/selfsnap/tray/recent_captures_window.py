from __future__ import annotations

import os
import subprocess
import tkinter as tk
from tkinter import ttk

from selfsnap.db import connect
from selfsnap.models import CaptureRecord
from selfsnap.paths import AppPaths
from selfsnap.records import get_recent


def show_recent_captures_window(paths: AppPaths) -> None:
    """Open a compact window showing the last 10 captures with thumbnails."""
    try:
        from PIL import Image, ImageTk
        pil_available = True
    except ImportError:
        pil_available = False

    root = tk.Toplevel()
    root.title("Recent Captures")
    root.resizable(False, False)
    root.geometry("640x480")

    with connect(paths.db_path) as conn:
        records = get_recent(conn, n=10)

    if not records:
        ttk.Label(root, text="No captures yet.", padding=20).pack()
        ttk.Button(root, text="Close", command=root.destroy).pack(pady=8)
        return

    frame = ttk.Frame(root, padding=8)
    frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(frame, highlightthickness=0)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))

    _thumb_refs: list[object] = []  # prevent GC

    for row_idx, record in enumerate(records):
        row_frame = ttk.Frame(inner, padding=(4, 4))
        row_frame.grid(row=row_idx, column=0, sticky="ew")

        thumb_label = ttk.Label(row_frame, width=12)
        thumb_label.grid(row=0, column=0, rowspan=2, padx=(0, 8))

        if pil_available and record.image_path and os.path.exists(record.image_path):
            try:
                img = Image.open(record.image_path)
                img.thumbnail((96, 64))
                photo = ImageTk.PhotoImage(img)
                thumb_label.configure(image=photo)  # type: ignore[arg-type]
                _thumb_refs.append(photo)
            except Exception:
                thumb_label.configure(text="[no preview]")
        else:
            thumb_label.configure(text="[no preview]")

        ts = (record.started_utc or record.created_utc or "")[:19].replace("T", " ")
        trigger = record.trigger_source.capitalize()
        info_text = f"{ts}  ·  {trigger}"
        if record.schedule_id:
            info_text += f"  ·  {record.schedule_id}"
        ttk.Label(row_frame, text=info_text, font=("TkDefaultFont", 9, "bold")).grid(
            row=0, column=1, sticky="w"
        )
        outcome_text = f"{record.outcome_category}  ·  {record.outcome_code}"
        outcome_label = ttk.Label(row_frame, text=outcome_text, font=("TkDefaultFont", 8))
        outcome_label.grid(row=1, column=1, sticky="w")

        # S3.1.2 — tooltip with full detail
        tooltip_text = (
            f"Trigger: {record.trigger_source}\n"
            f"Started: {record.started_utc}\n"
            f"Outcome: {record.outcome_category} / {record.outcome_code}\n"
            f"Path: {record.image_path or '(none)'}"
        )
        _bind_tooltip(thumb_label, tooltip_text)
        _bind_tooltip(outcome_label, tooltip_text)

        if record.image_path and os.path.exists(record.image_path):
            path = record.image_path
            open_btn = ttk.Button(
                row_frame,
                text="Open",
                width=6,
                command=lambda p=path: _open_file(p),
            )
            open_btn.grid(row=0, column=2, rowspan=2, padx=(8, 0))

        ttk.Separator(inner, orient="horizontal").grid(
            row=row_idx * 2 + 1, column=0, sticky="ew", pady=2
        )

    ttk.Button(root, text="Close", command=root.destroy).pack(pady=8)
    root.mainloop()


def _open_file(path: str) -> None:
    try:
        os.startfile(path)  # type: ignore[attr-defined]
    except Exception:
        subprocess.Popen(["explorer", path])


def _bind_tooltip(widget: tk.Widget, text: str) -> None:
    tip_window: list[tk.Toplevel | None] = [None]

    def _show(_event: tk.Event) -> None:  # type: ignore[type-arg]
        if tip_window[0]:
            return
        x = widget.winfo_rootx() + 20
        y = widget.winfo_rooty() + 20
        tip = tk.Toplevel(widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        tk.Label(tip, text=text, justify="left", background="#ffffcc", relief="solid", borderwidth=1,
                 font=("TkDefaultFont", 8)).pack()
        tip_window[0] = tip

    def _hide(_event: tk.Event) -> None:  # type: ignore[type-arg]
        if tip_window[0]:
            tip_window[0].destroy()
            tip_window[0] = None

    widget.bind("<Enter>", _show)
    widget.bind("<Leave>", _hide)
