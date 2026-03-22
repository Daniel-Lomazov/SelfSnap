from __future__ import annotations

import importlib
import types

from selfsnap.runtime_probe import probe_runtime_dependencies


def test_runtime_probe_reports_success(monkeypatch) -> None:
    modules = {
        "pystray": types.SimpleNamespace(),
        "PIL": types.SimpleNamespace(__version__="12.1.1"),
        "PIL.Image": types.SimpleNamespace(__file__="C:/fake/PIL/Image.py"),
        "PIL._imaging": types.SimpleNamespace(__file__="C:/fake/PIL/_imaging.pyd"),
        "mss": types.SimpleNamespace(),
    }

    def fake_import(name: str):
        return modules[name]

    monkeypatch.setattr(importlib, "import_module", fake_import)

    result = probe_runtime_dependencies()

    assert result.ok is True
    assert result.classification == "ok"
    assert result.pillow_version == "12.1.1"
    assert result.pillow_path == "C:/fake/PIL/Image.py"


def test_runtime_probe_reports_broken_native_dependency(monkeypatch) -> None:
    def fake_import(name: str):
        if name == "PIL._imaging":
            raise ImportError("DLL load failed while importing _imaging")
        return types.SimpleNamespace(__file__="C:/fake/module.py")

    monkeypatch.setattr(importlib, "import_module", fake_import)

    result = probe_runtime_dependencies()

    assert result.ok is False
    assert result.classification == "broken_native_dependency"
    assert "DLL load failed while importing _imaging" in result.details
