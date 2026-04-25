from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from selfsnap.lifecycle_actions import (
    launch_and_confirm,
    resolve_reinstall_invocation,
    resolve_restart_invocation,
    resolve_tray_relaunch_after_exit_invocation,
    resolve_uninstall_invocation,
    run_lifecycle_script_and_check,
    schedule_tray_relaunch_after_exit,
)
from selfsnap.runtime_launch import LaunchSpec


def test_resolve_restart_invocation_uses_tray_background_launch(temp_paths, monkeypatch) -> None:
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_tray_background_invocation",
        lambda _paths: object(),
    )

    result = resolve_restart_invocation(temp_paths)

    assert result is not None


def test_resolve_reinstall_invocation_targets_reinstall_script(temp_paths, monkeypatch) -> None:
    scripts_dir = temp_paths.user_profile / "scripts" / "user"
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
    scripts_dir = temp_paths.user_profile / "scripts" / "user"
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


def test_resolve_tray_relaunch_after_exit_invocation_waits_then_launches(
    temp_paths, monkeypatch
) -> None:
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_tray_background_invocation",
        lambda _paths: type(
            "Spec",
            (),
            {
                "executable": r"C:\Python312\pythonw.exe",
                "arguments": ["-m", "selfsnap", "tray"],
                "working_directory": str(temp_paths.root),
            },
        )(),
    )

    spec = resolve_tray_relaunch_after_exit_invocation(temp_paths, wait_for_process_id=4242)

    assert spec.executable.lower() == "powershell.exe"
    assert "-Command" in spec.arguments
    command = spec.arguments[spec.arguments.index("-Command") + 1]
    assert "Wait-Process -Id 4242" in command
    assert "Start-Process -FilePath 'C:\\Python312\\pythonw.exe'" in command
    assert "-ArgumentList @('-m', 'selfsnap', 'tray')" in command


def test_schedule_tray_relaunch_after_exit_returns_false_if_helper_exits(
    temp_paths, monkeypatch
) -> None:
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_tray_relaunch_after_exit_invocation",
        lambda _paths, wait_for_process_id: object(),
    )

    class ExitedProcess:
        def poll(self):
            return 1

    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.launch_hidden_background",
        lambda _spec: ExitedProcess(),
    )

    assert schedule_tray_relaunch_after_exit(temp_paths, wait_for_process_id=4242) is False


def test_resolve_reinstall_invocation_raises_when_script_is_missing(
    temp_paths, monkeypatch
) -> None:
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

    with pytest.raises(RuntimeError, match=r"reinstall\.ps1"):
        resolve_reinstall_invocation(temp_paths, update_source=True)


def test_schedule_tray_relaunch_after_exit_returns_true_when_process_has_no_poll(
    temp_paths, monkeypatch
) -> None:
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_tray_relaunch_after_exit_invocation",
        lambda _paths, wait_for_process_id: object(),
    )

    class NoPollProcess:
        pass

    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.launch_hidden_background",
        lambda _spec: NoPollProcess(),
    )

    assert schedule_tray_relaunch_after_exit(temp_paths, wait_for_process_id=4242) is True


@pytest.mark.parametrize(
    ("poll_values", "monotonic_values", "expected"),
    [
        ([1], [0.0, 0.1], False),
        ([None, None], [0.0, 0.1, 0.6], True),
    ],
)
def test_launch_and_confirm_tracks_process_liveness(
    monkeypatch, temp_paths, poll_values, monotonic_values, expected
) -> None:
    remaining_polls = list(poll_values)
    monotonic_iter = iter(monotonic_values)

    class FakeProcess:
        def poll(self):
            if remaining_polls:
                return remaining_polls.pop(0)
            return poll_values[-1]

    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.launch_background",
        lambda _spec: FakeProcess(),
    )
    monkeypatch.setattr("time.monotonic", lambda: next(monotonic_iter))
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    spec = LaunchSpec(
        executable="pythonw.exe",
        arguments=["-m", "selfsnap", "tray"],
        working_directory=str(temp_paths.root),
    )

    assert launch_and_confirm(spec, wait_seconds=0.5) is expected


@pytest.mark.parametrize(("returncode", "expected"), [(0, True), (1, False)])
def test_run_lifecycle_script_and_check_uses_completed_return_code(
    monkeypatch, temp_paths, returncode, expected
) -> None:
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.run_lifecycle_script",
        lambda _spec: subprocess.CompletedProcess(args=["powershell.exe"], returncode=returncode),
    )

    spec = LaunchSpec(
        executable="powershell.exe",
        arguments=["-File", "script.ps1"],
        working_directory=str(temp_paths.root),
    )

    assert run_lifecycle_script_and_check(spec) is expected
