from __future__ import annotations

import tkinter as tk

import pytest

from selfsnap.ui.fluent import apply_fluent_window


def test_apply_fluent_window_allows_default_label_creation() -> None:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk unavailable in test environment: {exc}")

    try:
        root.withdraw()
        apply_fluent_window(root)

        label = tk.Label(root, text="Settings")

        assert label.winfo_exists() == 1
    finally:
        root.destroy()