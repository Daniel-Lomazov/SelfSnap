from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
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
    _pin_job_ids: list[str] = field(default_factory=list)

    def _pin_once(self) -> None:
        self.canvas.yview_moveto(0.0)

    def _schedule_pin_job(self, delay: int | None) -> None:
        job_id_holder: list[str | None] = [None]

        def _callback() -> None:
            job_id = job_id_holder[0]
            if job_id is not None:
                try:
                    self._pin_job_ids.remove(job_id)
                except ValueError:
                    pass
            self._pin_once()

        if delay is None:
            job_id = self.canvas.after_idle(_callback)
        else:
            job_id = self.canvas.after(delay, _callback)
        job_id_holder[0] = job_id
        self._pin_job_ids.append(job_id)

    def pin_to_top(self, *, passes: int = 1) -> None:
        for job_id in self._pin_job_ids:
            try:
                self.canvas.after_cancel(job_id)
            except tk.TclError:
                continue
        self._pin_job_ids.clear()

        self._pin_once()

        follow_up_delays: tuple[int | None, ...] = (None, 24, 72, 144)
        for delay in follow_up_delays[: max(passes - 1, 0)]:
            self._schedule_pin_job(delay)


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
    root.option_add("*Font", ("Segoe UI", 10))
    root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))
    style = ttk.Style(root)
    style.configure("TNotebook", background=WINDOW_BG, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(6, 3), font=("Segoe UI Semibold", 10))
    style.configure("TButton", padding=(8, 4))
    style.configure("Small.TButton", padding=(6, 3))
    style.configure("Wide.TButton", padding=(10, 5))
    style.configure("TCombobox", padding=2)
    style.configure("TCheckbutton", padding=1)
    try:
        style.map(
            "TNotebook.Tab",
            background=[("selected", CARD_BG), ("!selected", WINDOW_BG)],
            foreground=[("selected", TEXT_PRIMARY), ("!selected", TEXT_SECONDARY)],
        )
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
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
    page = ScrollablePage(container=container, canvas=canvas, content=content)

    def _sync_canvas(_event=None) -> None:
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfigure(window_id, width=canvas.winfo_width())

    content.bind("<Configure>", _sync_canvas)
    canvas.bind("<Configure>", _sync_canvas)
    return page


def bind_dynamic_wrap(
    container: tk.Misc,
    root: tk.Misc,
    widget: tk.Label,
    *,
    padding: int = 56,
    minimum: int = 280,
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
        font=("Segoe UI Semibold", 7),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")

    title_row = tk.Frame(frame, bg=WINDOW_BG)
    title_row.grid(row=1, column=0, sticky="ew", pady=(2, 0))
    title_row.columnconfigure(0, weight=1)
    tk.Label(
        title_row,
        text=title,
        bg=WINDOW_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 16),
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
        font=("Segoe UI", 8),
        justify="left",
        anchor="w",
    )
    subtitle_label.grid(row=2, column=0, sticky="ew", pady=(2, 0))
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
        title_font=("Segoe UI Semibold", 12),
        title_pad=(10, 8, 10, 0),
        body_pad=(10, 8),
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
        title_font=("Segoe UI Semibold", 10),
        title_pad=(6, 6, 6, 0),
        body_pad=(6, 6),
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
        font=("Segoe UI", 9),
        justify="left",
        anchor="w",
    )
    summary_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))

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
        font=("Segoe UI Semibold", 8),
        padx=6,
        pady=2,
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
