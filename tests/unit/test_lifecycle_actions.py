from __future__ import annotations

from pathlib import Path

from selfsnap.lifecycle_actions import (
    resolve_reinstall_invocation,
    resolve_restart_invocation,
    resolve_uninstall_invocation,
)


def test_resolve_restart_invocation_uses_tray_background_launch(temp_paths, monkeypatch) -> None:
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_tray_background_invocation",
        lambda _paths: object(),
    )

    result = resolve_restart_invocation(temp_paths)

    assert result is not None


def test_resolve_reinstall_invocation_targets_reinstall_script(temp_paths, monkeypatch) -> None:
    scripts_dir = temp_paths.user_profile / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "reinstall.ps1").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_source_repo_root",
        lambda _paths: str(temp_paths.user_profile),
    )
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_foreground_python_executable",
        lambda _paths: r"C:\Python312\python.exe",
    )
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_background_python_executable",
        lambda _paths: r"C:\Python312\pythonw.exe",
    )

    spec = resolve_reinstall_invocation(temp_paths, update_source=True, relaunch_tray=True)

    assert spec.executable.lower() == "powershell.exe"
    file_idx = spec.arguments.index("-File")
    assert Path(spec.arguments[file_idx + 1]).name == "reinstall.ps1"
    assert "-UpdateSource" in spec.arguments
    assert "-RelaunchTray" in spec.arguments
    assert r"C:\Python312\python.exe" in spec.arguments
    assert r"C:\Python312\pythonw.exe" in spec.arguments
    assert spec.working_directory == str(temp_paths.user_profile)


def test_resolve_uninstall_invocation_targets_uninstall_script(temp_paths, monkeypatch) -> None:
    scripts_dir = temp_paths.user_profile / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "uninstall.ps1").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_source_repo_root",
        lambda _paths: str(temp_paths.user_profile),
    )
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_foreground_python_executable",
        lambda _paths: r"C:\Python312\python.exe",
    )

    spec = resolve_uninstall_invocation(temp_paths, remove_user_data=True)

    assert spec.executable.lower() == "powershell.exe"
    file_idx = spec.arguments.index("-File")
    assert Path(spec.arguments[file_idx + 1]).name == "uninstall.ps1"
    assert "-RemoveUserData" in spec.arguments
    assert r"C:\Python312\python.exe" in spec.arguments
