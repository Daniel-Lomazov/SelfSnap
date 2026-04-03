from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk

from selfsnap.tray.ui_presenters import disclosure_button_label


@dataclass(slots=True)
class DisclosureSection:
    container: ttk.Frame
    body: ttk.Frame
    _toggle_button: ttk.Button
    _summary_var: tk.StringVar
    _title: str
    _expanded: bool
    _on_toggle: Callable[[], None] | None = None

    def set_summary(self, value: str) -> None:
        self._summary_var.set(value)

    def toggle(self) -> None:
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = expanded
        self._toggle_button.configure(text=disclosure_button_label(self._title, expanded))
        if expanded:
            self.body.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        else:
            self.body.grid_remove()
        if self._on_toggle is not None:
            self._on_toggle()


def apply_focus_minimal_styles(root: tk.Tk) -> None:
    style = ttk.Style(root)
    style.configure("FocusHero.TFrame")
    style.configure("FocusHeroTitle.TLabel", font=("Segoe UI Semibold", 15))
    style.configure("FocusSectionTitle.TLabel", font=("Segoe UI Semibold", 10))
    style.configure("FocusMuted.TLabel", foreground="#475569")
    style.configure("FocusStatus.TLabel", font=("Segoe UI Semibold", 10))
    style.configure("FocusAction.TButton", padding=(12, 6))
    style.configure("FocusToggle.TButton", padding=(10, 4))
    style.configure("Treeview", rowheight=24)


def create_disclosure_section(
    parent: ttk.Frame,
    *,
    title: str,
    summary: str,
    expanded: bool,
    on_toggle: Callable[[], None] | None = None,
) -> DisclosureSection:
    container = ttk.Frame(parent, padding=(12, 10))
    container.columnconfigure(0, weight=1)

    header = ttk.Frame(container)
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(0, weight=1)

    title_label = ttk.Label(header, text=title, style="FocusSectionTitle.TLabel")
    title_label.grid(row=0, column=0, sticky="w")

    summary_var = tk.StringVar(master=container, value=summary)
    summary_label = ttk.Label(header, textvariable=summary_var, style="FocusMuted.TLabel")
    summary_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

    toggle_button = ttk.Button(header, style="FocusToggle.TButton")
    toggle_button.grid(row=0, column=1, rowspan=2, sticky="e")

    body = ttk.Frame(container)
    body.columnconfigure(0, weight=1)

    section = DisclosureSection(
        container=container,
        body=body,
        _toggle_button=toggle_button,
        _summary_var=summary_var,
        _title=title,
        _expanded=expanded,
        _on_toggle=on_toggle,
    )
    toggle_button.configure(command=section.toggle)
    section.set_expanded(expanded)
    return section