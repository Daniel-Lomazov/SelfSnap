from __future__ import annotations

from datetime import datetime
import os
import subprocess
import tkinter as tk
from tkinter import ttk

from selfsnap.db import connect
from selfsnap.models import CaptureRecord
from selfsnap.paths import AppPaths
from selfsnap.records import get_recent


REFRESH_INTERVAL_MS = 5000


def show_recent_captures_window(paths: AppPaths) -> None:
    """Open a compact window showing recent captures with thumbnails and live updates."""
    try:
        from PIL import Image, ImageTk
        pil_available = True
    except ImportError:
        pil_available = False
        Image = None
        ImageTk = None

    root = tk.Tk()
    root.title("Recent Captures")
    root.resizable(False, False)
    root.geometry("640x480")

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

    status_label = ttk.Label(root, text="Auto-refreshes every 5 seconds", padding=(8, 0))
    status_label.pack(anchor="w")

    _thumb_refs: list[object] = []  # prevent GC for PhotoImage objects
    refresh_job: str | None = None
    last_snapshot: tuple[str, ...] = ()

    def _render(records: list[CaptureRecord]) -> None:
        for child in inner.winfo_children():
            child.destroy()
        _thumb_refs.clear()

        if not records:
            ttk.Label(inner, text="No captures yet.", padding=20).grid(row=0, column=0, sticky="w")
            return

        for row_idx, record in enumerate(records):
            row_frame = ttk.Frame(inner, padding=(4, 4))
            row_frame.grid(row=row_idx * 2, column=0, sticky="ew")

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

            ts_utc = record.started_utc or record.created_utc or ""
            ts_local = _format_local_timestamp(ts_utc)
            trigger = record.trigger_source.capitalize()
            info_text = f"{ts_local}  ·  {trigger}"
            if record.schedule_id:
                info_text += f"  ·  {record.schedule_id}"
            ttk.Label(row_frame, text=info_text, font=("TkDefaultFont", 9, "bold")).grid(
                row=0, column=1, sticky="w"
            )
            outcome_text = f"{record.outcome_category}  ·  {record.outcome_code}"
            outcome_label = ttk.Label(row_frame, text=outcome_text, font=("TkDefaultFont", 8))
            outcome_label.grid(row=1, column=1, sticky="w")

            tooltip_text = (
                f"Trigger: {record.trigger_source}\n"
                f"Started (local): {ts_local}\n"
                f"Started (UTC): {record.started_utc or record.created_utc}\n"
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

    def _snapshot(records: list[CaptureRecord]) -> tuple[str, ...]:
        return tuple(record.record_id for record in records)

    def _refresh() -> None:
        nonlocal refresh_job, last_snapshot
        with connect(paths.db_path) as conn:
            records = get_recent(conn, n=10)
        current_snapshot = _snapshot(records)
        if current_snapshot != last_snapshot:
            _render(records)
            last_snapshot = current_snapshot
        refresh_job = root.after(REFRESH_INTERVAL_MS, _refresh)

    def _on_close() -> None:
        if refresh_job is not None:
            try:
                root.after_cancel(refresh_job)
            except tk.TclError:
                pass
        root.destroy()

    _refresh()

    ttk.Button(root, text="Close", command=_on_close).pack(pady=8)
    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


def _format_local_timestamp(utc_text: str) -> str:
    if not utc_text:
        return "(unknown time)"
    text = utc_text.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return utc_text[:19].replace("T", " ")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.now().astimezone().tzinfo)
    local_dt = parsed.astimezone()
    return local_dt.strftime("%Y-%m-%d %H:%M:%S")


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
