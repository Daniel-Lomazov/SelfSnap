from __future__ import annotations

import tkinter as tk

import pytest

from selfsnap.ui.fluent import create_scrollable_page


def test_scrollable_page_pin_to_top_survives_late_configure() -> None:
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable")

    try:
        root.geometry("280x180")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        page = create_scrollable_page(root)
        page.container.grid(row=0, column=0, sticky="nsew")
        page.content.columnconfigure(0, weight=1)

        for index in range(40):
            tk.Label(page.content, text=f"Row {index}").grid(row=index, column=0, sticky="w")

        for _ in range(3):
            root.update_idletasks()
            root.update()

        page.canvas.yview_moveto(1.0)
        root.update_idletasks()
        root.update()
        assert page.canvas.yview()[0] > 0.0

        page.pin_to_top(passes=3)
        root.geometry("300x180")
        for _ in range(5):
            root.update_idletasks()
            root.update()

        assert page.canvas.yview()[0] == pytest.approx(0.0, abs=1e-6)
    finally:
        root.destroy()
