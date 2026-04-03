from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

WINDOW_BG = "#f3f6fb"
CARD_BG = "#ffffff"
INSET_BG = "#f7fafe"
BORDER_COLOR = "#d8e1ec"
TEXT_PRIMARY = "#0f172a"
TEXT_SECONDARY = "#475569"
TEXT_MUTED = "#64748b"
ACCENT_COLOR = "#0b5cab"
ACCENT_BG = "#eaf3ff"
INFO_BG = "#eef6ff"
INFO_FG = "#0b5cab"
WARNING_BG = "#fff4dc"
WARNING_FG = "#8a4b00"
DANGER_BG = "#fdeaea"
DANGER_FG = "#971c1c"


@dataclass(slots=True)
class ScrollablePage:
    container: tk.Frame
    canvas: tk.Canvas
    content: tk.Frame


@dataclass(slots=True)
class PageHeader:
    frame: tk.Frame
    subtitle_label: tk.Label
    badge_label: tk.Label | None


@dataclass(slots=True)
class SectionBlock:
    frame: tk.Frame
    header: tk.Frame
    body: tk.Frame
    title_label: tk.Label
    summary_label: tk.Label
    badge_label: tk.Label | None


def apply_fluent_window(root: tk.Misc) -> None:
    root.configure(bg=WINDOW_BG)
    root.option_add("*Font", "Segoe UI 10")
    root.option_add("*TCombobox*Listbox.font", "Segoe UI 10")
    style = ttk.Style(root)
    style.configure("TButton", padding=(10, 6))
    style.configure("Small.TButton", padding=(8, 4))
    style.configure("Wide.TButton", padding=(14, 8))
    style.configure("TCombobox", padding=4)
    style.configure("TCheckbutton", padding=2)
    try:
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10))
        style.map(
            "Treeview",
            background=[("selected", ACCENT_BG)],
            foreground=[("selected", TEXT_PRIMARY)],
        )
    except tk.TclError:
        return


def create_scrollable_page(parent: tk.Misc) -> ScrollablePage:
    container = tk.Frame(parent, bg=WINDOW_BG)
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, weight=1)

    canvas = tk.Canvas(
        container,
        bg=WINDOW_BG,
        highlightthickness=0,
        bd=0,
        relief="flat",
    )
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=scrollbar.set)

    content = tk.Frame(canvas, bg=WINDOW_BG)
    window_id = canvas.create_window((0, 0), window=content, anchor="nw")

    def _sync_canvas(_event=None) -> None:
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfigure(window_id, width=canvas.winfo_width())

    content.bind("<Configure>", _sync_canvas)
    canvas.bind("<Configure>", _sync_canvas)
    return ScrollablePage(container=container, canvas=canvas, content=content)


def bind_dynamic_wrap(
    container: tk.Misc,
    root: tk.Misc,
    widget: tk.Label,
    *,
    padding: int = 56,
    minimum: int = 380,
) -> None:
    def _update_wrap(_event=None) -> None:
        wrap = max(container.winfo_width() - padding, minimum)
        widget.configure(wraplength=wrap)

    container.bind("<Configure>", _update_wrap, add="+")
    root.after_idle(_update_wrap)


def create_page_header(
    parent: tk.Misc,
    *,
    eyebrow: str,
    title: str,
    subtitle: str,
    badge_text: str | None = None,
    badge_tone: str = "neutral",
) -> PageHeader:
    frame = tk.Frame(parent, bg=WINDOW_BG)
    frame.columnconfigure(0, weight=1)

    tk.Label(
        frame,
        text=eyebrow.upper(),
        bg=WINDOW_BG,
        fg=ACCENT_COLOR,
        font=("Segoe UI Semibold", 9),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")

    title_row = tk.Frame(frame, bg=WINDOW_BG)
    title_row.grid(row=1, column=0, sticky="ew", pady=(6, 0))
    title_row.columnconfigure(0, weight=1)
    tk.Label(
        title_row,
        text=title,
        bg=WINDOW_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 20),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")

    badge_label: tk.Label | None = None
    if badge_text:
        badge_label = _create_pill(title_row, badge_text, tone=badge_tone)
        badge_label.grid(row=0, column=1, sticky="e")

    subtitle_label = tk.Label(
        frame,
        text=subtitle,
        bg=WINDOW_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
        justify="left",
        anchor="w",
    )
    subtitle_label.grid(row=2, column=0, sticky="ew", pady=(8, 0))
    return PageHeader(frame=frame, subtitle_label=subtitle_label, badge_label=badge_label)


def create_card(
    parent: tk.Misc,
    *,
    title: str,
    summary: str,
    badge_text: str | None = None,
    tone: str = "neutral",
) -> SectionBlock:
    return _create_section(
        parent,
        title=title,
        summary=summary,
        badge_text=badge_text,
        tone=tone,
        background=CARD_BG,
        title_font=("Segoe UI Semibold", 13),
        title_pad=(18, 18, 18, 0),
        body_pad=(18, 18),
    )


def create_inset_panel(
    parent: tk.Misc,
    *,
    title: str,
    summary: str,
    tone: str = "neutral",
) -> SectionBlock:
    return _create_section(
        parent,
        title=title,
        summary=summary,
        badge_text=None,
        tone=tone,
        background=INSET_BG,
        title_font=("Segoe UI Semibold", 11),
        title_pad=(14, 14, 14, 0),
        body_pad=(14, 14),
    )


def _create_section(
    parent: tk.Misc,
    *,
    title: str,
    summary: str,
    badge_text: str | None,
    tone: str,
    background: str,
    title_font: tuple[str, int] | tuple[str, int, str],
    title_pad: tuple[int, int, int, int],
    body_pad: tuple[int, int],
) -> SectionBlock:
    frame = tk.Frame(
        parent,
        bg=background,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
        bd=0,
    )
    frame.columnconfigure(0, weight=1)

    header = tk.Frame(
        frame,
        bg=background,
        padx=title_pad[0],
        pady=title_pad[1],
    )
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(0, weight=1)

    title_label = tk.Label(
        header,
        text=title,
        bg=background,
        fg=TEXT_PRIMARY,
        font=title_font,
        anchor="w",
    )
    title_label.grid(row=0, column=0, sticky="w")

    badge_label: tk.Label | None = None
    if badge_text:
        badge_label = _create_pill(header, badge_text, tone=tone)
        badge_label.grid(row=0, column=1, sticky="e")

    summary_label = tk.Label(
        header,
        text=summary,
        bg=background,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
        justify="left",
        anchor="w",
    )
    summary_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    body = tk.Frame(frame, bg=background, padx=body_pad[0], pady=body_pad[1])
    body.grid(row=1, column=0, sticky="nsew")
    return SectionBlock(
        frame=frame,
        header=header,
        body=body,
        title_label=title_label,
        summary_label=summary_label,
        badge_label=badge_label,
    )


def _create_pill(parent: tk.Misc, text: str, *, tone: str) -> tk.Label:
    bg, fg = _pill_colors(tone)
    return tk.Label(
        parent,
        text=text,
        bg=bg,
        fg=fg,
        font=("Segoe UI Semibold", 9),
        padx=10,
        pady=4,
    )


def _pill_colors(tone: str) -> tuple[str, str]:
    if tone == "accent":
        return ACCENT_BG, ACCENT_COLOR
    if tone == "info":
        return INFO_BG, INFO_FG
    if tone == "warning":
        return WARNING_BG, WARNING_FG
    if tone == "danger":
        return DANGER_BG, DANGER_FG
    return "#edf2f7", TEXT_SECONDARY
