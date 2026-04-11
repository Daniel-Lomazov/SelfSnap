from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from selfsnap.runtime_launch import (
    LaunchSpec,
    launch_background,
    launch_hidden_background,
    resolve_background_working_directory,
    resolve_background_python_executable,
    resolve_foreground_python_executable,
    resolve_manual_capture_background_invocation,
    resolve_source_repo_root,
    run_background_command,
    run_lifecycle_script,
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
        '{"repo_root": "'
        + str(temp_paths.user_profile).replace("\\", "\\\\")
        + '"}',
        encoding="utf-8",
    )

    result = resolve_source_repo_root(temp_paths)

    assert Path(result) == temp_paths.user_profile


def test_launch_background_requests_text_mode(monkeypatch, temp_paths) -> None:
    captured: dict[str, object] = {}

    def fake_popen(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("selfsnap.runtime_launch.subprocess.Popen", fake_popen)
    spec = LaunchSpec(
        executable="pythonw.exe",
        arguments=["-m", "selfsnap", "tray"],
        working_directory=str(temp_paths.root),
    )

    launch_background(spec)

    assert captured["args"] == (spec.command(),)
    kwargs = captured["kwargs"]
    assert kwargs["cwd"] == spec.working_directory
    assert kwargs["text"] is True
    assert kwargs["close_fds"] is False


def test_launch_hidden_background_suppresses_stdio_and_requests_text_mode(
    monkeypatch, temp_paths
) -> None:
    captured: dict[str, object] = {}

    def fake_popen(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("selfsnap.runtime_launch.subprocess.Popen", fake_popen)
    spec = LaunchSpec(
        executable="powershell.exe",
        arguments=["-File", "script.ps1"],
        working_directory=str(temp_paths.root),
    )

    launch_hidden_background(spec)

    kwargs = captured["kwargs"]
    assert kwargs["cwd"] == spec.working_directory
    assert kwargs["stdout"] is subprocess.DEVNULL
    assert kwargs["stderr"] is subprocess.DEVNULL
    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["text"] is True
    assert kwargs["close_fds"] is False


@pytest.mark.parametrize(
    ("runner_name", "expected_stdio"),
    [
        ("run_background_command", {}),
        (
            "run_lifecycle_script",
            {
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
                "stdin": subprocess.DEVNULL,
            },
        ),
    ],
)
def test_run_helpers_request_text_mode(monkeypatch, temp_paths, runner_name, expected_stdio) -> None:
    captured: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=args[0], returncode=0)

    monkeypatch.setattr("selfsnap.runtime_launch.subprocess.run", fake_run)
    spec = LaunchSpec(
        executable="python.exe",
        arguments=["-m", "selfsnap", "capture"],
        working_directory=str(temp_paths.root),
    )

    if runner_name == "run_background_command":
        run_background_command(spec)
    else:
        run_lifecycle_script(spec)

    assert captured["args"] == (spec.command(),)
    kwargs = captured["kwargs"]
    assert kwargs["cwd"] == spec.working_directory
    assert kwargs["text"] is True
    for key, value in expected_stdio.items():
        assert kwargs[key] is value
