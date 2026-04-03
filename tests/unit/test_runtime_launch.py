from __future__ import annotations

from pathlib import Path

import pytest

from selfsnap.runtime_launch import (
    resolve_background_python_executable,
    resolve_background_working_directory,
    resolve_foreground_python_executable,
    resolve_manual_capture_background_invocation,
    resolve_source_repo_root,
)


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


def test_resolve_background_python_executable_ignores_stale_metadata(
    monkeypatch, temp_paths
) -> None:
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


def test_resolve_background_python_executable_uses_python_metadata_sibling(temp_paths) -> None:
    temp_paths.bin_dir.mkdir(parents=True, exist_ok=True)
    metadata_python = temp_paths.bin_dir / "python.exe"
    metadata_python.write_text("", encoding="utf-8")
    metadata_pythonw = temp_paths.bin_dir / "pythonw.exe"
    metadata_pythonw.write_text("", encoding="utf-8")
    (temp_paths.bin_dir / "install-meta.json").write_text(
        '{"python_executable": "'
        + str(metadata_python).replace("\\", "\\\\")
        + '", "repo_root": "'
        + str(temp_paths.user_profile).replace("\\", "\\\\")
        + '"}',
        encoding="utf-8",
    )

    result = resolve_background_python_executable(temp_paths)

    assert Path(result) == metadata_pythonw


def test_resolve_background_python_executable_uses_metadata_python_sibling_when_pythonw_is_stale(
    temp_paths,
) -> None:
    temp_paths.bin_dir.mkdir(parents=True, exist_ok=True)
    metadata_python = temp_paths.bin_dir / "python.exe"
    metadata_python.write_text("", encoding="utf-8")
    metadata_pythonw = temp_paths.bin_dir / "pythonw.exe"
    metadata_pythonw.write_text("", encoding="utf-8")
    (temp_paths.bin_dir / "install-meta.json").write_text(
        '{"python_executable": "'
        + str(metadata_python).replace("\\", "\\\\")
        + '", "pythonw_executable": "C:\\\\missing\\\\pythonw.exe", "repo_root": "'
        + str(temp_paths.user_profile).replace("\\", "\\\\")
        + '"}',
        encoding="utf-8",
    )

    result = resolve_background_python_executable(temp_paths)

    assert Path(result) == metadata_pythonw


def test_resolve_background_python_executable_raises_without_pythonw(monkeypatch) -> None:
    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", r"C:\Temp\python.exe")

    with pytest.raises(RuntimeError):
        resolve_background_python_executable()


def test_resolve_background_working_directory_ignores_stale_metadata(temp_paths) -> None:
    temp_paths.bin_dir.mkdir(parents=True, exist_ok=True)
    (temp_paths.bin_dir / "install-meta.json").write_text(
        '{"repo_root": "C:\\\\missing-repo"}',
        encoding="utf-8",
    )

    result = resolve_background_working_directory(temp_paths)

    assert (Path(result) / "pyproject.toml").exists()


def test_resolve_manual_capture_background_invocation_uses_pythonw_and_repo_root(
    temp_paths, monkeypatch
) -> None:
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
    monkeypatch.setattr("selfsnap.runtime_launch.sys.frozen", False, raising=False)

    spec = resolve_manual_capture_background_invocation(temp_paths)

    assert Path(spec.executable) == pythonw
    assert spec.arguments == ["-m", "selfsnap", "capture", "--trigger", "manual"]
    assert spec.working_directory == str(temp_paths.user_profile)


def test_resolve_foreground_python_executable_prefers_install_metadata(temp_paths) -> None:
    temp_paths.bin_dir.mkdir(parents=True, exist_ok=True)
    python_executable = temp_paths.bin_dir / "python.exe"
    python_executable.write_text("", encoding="utf-8")
    (temp_paths.bin_dir / "install-meta.json").write_text(
        '{"python_executable": "'
        + str(python_executable).replace("\\", "\\\\")
        + '", "repo_root": "'
        + str(temp_paths.user_profile).replace("\\", "\\\\")
        + '"}',
        encoding="utf-8",
    )

    result = resolve_foreground_python_executable(temp_paths)

    assert Path(result) == python_executable


def test_resolve_source_repo_root_prefers_trusted_install_metadata(temp_paths) -> None:
    temp_paths.bin_dir.mkdir(parents=True, exist_ok=True)
    (temp_paths.bin_dir / "install-meta.json").write_text(
        '{"repo_root": "' + str(temp_paths.user_profile).replace("\\", "\\\\") + '"}',
        encoding="utf-8",
    )

    result = resolve_source_repo_root(temp_paths)

    assert Path(result) == temp_paths.user_profile
