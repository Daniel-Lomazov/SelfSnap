from __future__ import annotations

from pathlib import Path

import pytest

from selfsnap.runtime_launch import resolve_background_python_executable


def test_resolve_background_python_executable_prefers_install_metadata(temp_paths) -> None:
    temp_paths.bin_dir.mkdir(parents=True, exist_ok=True)
    pythonw = temp_paths.bin_dir / "pythonw.exe"
    pythonw.write_text("", encoding="utf-8")
    (temp_paths.bin_dir / "install-meta.json").write_text(
        '{"pythonw_executable": "'
        + str(pythonw).replace("\\", "\\\\")
        + '", "repo_root": "'
        + str(temp_paths.user_profile).replace("\\", "\\\\")
        + '"}',
        encoding="utf-8",
    )

    result = resolve_background_python_executable(temp_paths)

    assert Path(result) == pythonw


def test_resolve_background_python_executable_ignores_stale_metadata(monkeypatch, temp_paths) -> None:
    temp_paths.bin_dir.mkdir(parents=True, exist_ok=True)
    stale_pythonw = temp_paths.bin_dir / "stale-pythonw.exe"
    stale_pythonw.write_text("", encoding="utf-8")
    (temp_paths.bin_dir / "install-meta.json").write_text(
        '{"pythonw_executable": "'
        + str(stale_pythonw).replace("\\", "\\\\")
        + '", "repo_root": "C:\\\\missing-repo"}',
        encoding="utf-8",
    )
    fallback_python = temp_paths.bin_dir / "python.exe"
    fallback_python.write_text("", encoding="utf-8")
    fallback_pythonw = temp_paths.bin_dir / "pythonw.exe"
    fallback_pythonw.write_text("", encoding="utf-8")
    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", str(fallback_python))

    result = resolve_background_python_executable(temp_paths)

    assert Path(result) == fallback_pythonw


def test_resolve_background_python_executable_raises_without_pythonw(monkeypatch) -> None:
    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", r"C:\Temp\python.exe")

    with pytest.raises(RuntimeError):
        resolve_background_python_executable()
