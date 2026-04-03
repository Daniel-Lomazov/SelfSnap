from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

_TONE_COLORS = {
    "good": "#166534",
    "warn": "#9a3412",
    "neutral": "#0f172a",
}


@dataclass(slots=True)
class DiagnosticCardWidgets:
    frame: ttk.Frame
    headline: ttk.Label
    detail: ttk.Label


def bind_wrap(container: tk.Misc, root: tk.Misc, widget: tk.Widget, *, padding: int = 56) -> None:
    def _update_wrap(_event=None) -> None:
        wrap = max(container.winfo_width() - padding, 380)
        try:
            widget.configure(wraplength=wrap)
        except tk.TclError:
            return

    container.bind("<Configure>", _update_wrap, add="+")
    root.after_idle(_update_wrap)


def create_diagnostic_card(parent: ttk.Frame, title: str) -> DiagnosticCardWidgets:
    frame = ttk.Frame(parent, padding=(10, 8))
    frame.columnconfigure(0, weight=1)
    ttk.Label(frame, text=title, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
    headline = ttk.Label(frame, justify="left", font=("Segoe UI", 12, "bold"))
    headline.grid(row=1, column=0, sticky="ew", pady=(6, 2))
    detail = ttk.Label(frame, justify="left", foreground="#334155")
    detail.grid(row=2, column=0, sticky="ew")
    return DiagnosticCardWidgets(frame=frame, headline=headline, detail=detail)


def bind_card_wrap(card: DiagnosticCardWidgets, root: tk.Misc, *, padding: int = 20) -> None:
    def _update_wrap(_event=None) -> None:
        wrap = max(card.frame.winfo_width() - padding, 180)
        for widget in (card.headline, card.detail):
            try:
                widget.configure(wraplength=wrap)
            except tk.TclError:
                continue

    card.frame.bind("<Configure>", _update_wrap, add="+")
    root.after_idle(_update_wrap)


def set_diagnostic_card_content(
    card: DiagnosticCardWidgets,
    *,
    headline: str,
    detail: str,
    tone: str = "neutral",
) -> None:
    card.headline.configure(
        text=headline, foreground=_TONE_COLORS.get(tone, _TONE_COLORS["neutral"])
    )
    card.detail.configure(text=detail)
