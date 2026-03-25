from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from selfsnap.db import connect
from selfsnap.paths import AppPaths
from selfsnap.records import daily_counts, summary_stats


def show_statistics_window(paths: AppPaths) -> None:
    """Open a window showing capture statistics and a 30-day bar chart."""
    root = tk.Toplevel()
    root.title("Capture Statistics")
    root.resizable(True, True)
    root.geometry("600x440")
    root.minsize(480, 360)

    with connect(paths.db_path) as conn:
        stats = summary_stats(conn)
        counts = daily_counts(conn, days=30)

    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)

    def _fmt(val: object) -> str:
        if val is None:
            return "0"
        if isinstance(val, int) and val >= 1024 * 1024:
            return f"{val / (1024*1024):.1f} MB"
        return str(val)

    labels = [
        ("Total Captures", "total_captures"),
        ("Successful", "total_success"),
        ("Missed", "total_missed"),
        ("Failed", "total_failed"),
        ("Skipped", "total_skipped"),
        ("Storage Used", "total_bytes"),
        ("Schedules Active", "distinct_schedules"),
    ]
    for row_i, (label, key) in enumerate(labels):
        ttk.Label(frame, text=label + ":", anchor="e").grid(row=row_i, column=0, sticky="e", pady=2, padx=(0, 8))
        ttk.Label(frame, text=_fmt(stats.get(key)), anchor="w", font=("TkDefaultFont", 10, "bold")).grid(
            row=row_i, column=1, sticky="w", pady=2
        )

    chart_frame = ttk.LabelFrame(frame, text="Captures — Last 30 Days", padding=8)
    chart_frame.grid(row=len(labels), column=0, columnspan=2, sticky="nsew", pady=(12, 0))
    chart_frame.columnconfigure(0, weight=1)
    chart_frame.rowconfigure(0, weight=1)
    frame.rowconfigure(len(labels), weight=1)

    canvas = tk.Canvas(chart_frame, height=160, highlightthickness=0, background="white")
    canvas.grid(row=0, column=0, sticky="nsew")

    def _draw_chart(_event: tk.Event | None = None) -> None:  # type: ignore[type-arg]
        canvas.delete("all")
        if not counts:
            canvas.create_text(
                canvas.winfo_width() // 2, 80,
                text="No data", fill="#999", font=("TkDefaultFont", 10)
            )
            return
        w = canvas.winfo_width() or 560
        h = canvas.winfo_height() or 160
        margin_l, margin_b, margin_t = 32, 24, 8
        max_count = max(c for _, c in counts)
        bar_area_w = w - margin_l - 4
        bar_w = max(1, bar_area_w // len(counts) - 1)
        bar_max_h = h - margin_b - margin_t
        for i, (day, count) in enumerate(counts):
            bar_h = int((count / max_count) * bar_max_h) if max_count else 0
            x0 = margin_l + i * (bar_w + 1)
            y0 = h - margin_b - bar_h
            x1 = x0 + bar_w
            y1 = h - margin_b
            canvas.create_rectangle(x0, y0, x1, y1, fill="#3b82f6", outline="")
            if i == 0 or i == len(counts) - 1:
                canvas.create_text(x0, h - margin_b + 4, text=day[5:], anchor="n", font=("TkDefaultFont", 7), fill="#555")

    canvas.bind("<Configure>", _draw_chart)
    root.after(100, _draw_chart)

    ttk.Button(root, text="Close", command=root.destroy).pack(pady=8)
