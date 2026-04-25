from __future__ import annotations

from selfsnap.ui.fluent import apply_fluent_window


class _FakeRoot:
    def __init__(self) -> None:
        self.configured: dict[str, object] = {}
        self.option_calls: list[tuple[str, object]] = []

    def configure(self, **kwargs: object) -> None:
        self.configured.update(kwargs)

    def option_add(self, pattern: str, value: object) -> None:
        self.option_calls.append((pattern, value))


class _FakeStyle:
    def __init__(self, _root: _FakeRoot) -> None:
        self.configures: list[tuple[str, dict[str, object]]] = []
        self.maps: list[tuple[str, dict[str, object]]] = []

    def configure(self, style_name: str, **kwargs: object) -> None:
        self.configures.append((style_name, kwargs))

    def map(self, style_name: str, **kwargs: object) -> None:
        self.maps.append((style_name, kwargs))


def test_apply_fluent_window_registers_tk_fonts_as_tuples(monkeypatch) -> None:
    fake_root = _FakeRoot()

    monkeypatch.setattr("selfsnap.ui.fluent.ttk.Style", _FakeStyle)

    apply_fluent_window(fake_root)

    assert fake_root.configured == {"bg": "#f3f6fb"}
    assert ("*Font", ("Segoe UI", 10)) in fake_root.option_calls
    assert ("*TCombobox*Listbox.font", ("Segoe UI", 10)) in fake_root.option_calls
