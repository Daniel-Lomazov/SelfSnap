from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from selfsnap.runtime_launch import (
    _background_creation_flags,
    _script_creation_flags,
    INTERPRETER_REDIRECT_ENV,
    LaunchSpec,
    ensure_local_repository_interpreter,
    launch_background,
    launch_hidden_background,
    read_install_metadata,
    resolve_background_python_executable,
    resolve_background_working_directory,
    resolve_foreground_python_executable,
    resolve_manual_capture_background_invocation,
    resolve_source_repo_root,
    resolve_tray_background_invocation,
    resolve_worker_background_invocation,
    run_background_command,
    run_lifecycle_script,
)


def _create_repo_checkout(repo_root: Path) -> None:
    (repo_root / "scripts" / "user").mkdir(parents=True, exist_ok=True)
    (repo_root / "scripts" / "user" / "setup.ps1").write_text("", encoding="utf-8")
    (repo_root / "pyproject.toml").write_text(
        "[project]\nname='selfsnap-win11'\n", encoding="utf-8"
    )


def _create_local_venv(repo_root: Path) -> tuple[Path, Path]:
    scripts_dir = repo_root / ".venv" / "Scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    python_executable = scripts_dir / "python.exe"
    pythonw_executable = scripts_dir / "pythonw.exe"
    python_executable.write_text("", encoding="utf-8")
    pythonw_executable.write_text("", encoding="utf-8")
    return python_executable, pythonw_executable


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
    checkout_root = temp_paths.user_profile / "not-a-checkout"
    checkout_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        "selfsnap.runtime_launch.resolve_source_repo_root",
        lambda _paths=None: str(checkout_root),
    )
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


def test_resolve_background_python_executable_raises_without_pythonw(monkeypatch, tmp_path) -> None:
    checkout_root = tmp_path / "not-a-checkout"
    checkout_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        "selfsnap.runtime_launch.resolve_source_repo_root",
        lambda _paths=None: str(checkout_root),
    )
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


def test_resolve_foreground_python_executable_prefers_local_repo_venv_over_metadata(
    temp_paths,
) -> None:
    repo_root = temp_paths.user_profile
    _create_repo_checkout(repo_root)
    local_python, _local_pythonw = _create_local_venv(repo_root)
    temp_paths.bin_dir.mkdir(parents=True, exist_ok=True)
    metadata_python = temp_paths.bin_dir / "python.exe"
    metadata_python.write_text("", encoding="utf-8")
    (temp_paths.bin_dir / "install-meta.json").write_text(
        '{"python_executable": "'
        + str(metadata_python).replace("\\", "\\\\")
        + '", "repo_root": "'
        + str(repo_root).replace("\\", "\\\\")
        + '"}',
        encoding="utf-8",
    )

    result = resolve_foreground_python_executable(temp_paths)

    assert Path(result) == local_python


def test_resolve_background_python_executable_prefers_local_repo_venv_over_metadata(
    temp_paths,
) -> None:
    repo_root = temp_paths.user_profile
    _create_repo_checkout(repo_root)
    _local_python, local_pythonw = _create_local_venv(repo_root)
    temp_paths.bin_dir.mkdir(parents=True, exist_ok=True)
    metadata_pythonw = temp_paths.bin_dir / "pythonw.exe"
    metadata_pythonw.write_text("", encoding="utf-8")
    (temp_paths.bin_dir / "install-meta.json").write_text(
        '{"pythonw_executable": "'
        + str(metadata_pythonw).replace("\\", "\\\\")
        + '", "repo_root": "'
        + str(repo_root).replace("\\", "\\\\")
        + '"}',
        encoding="utf-8",
    )

    result = resolve_background_python_executable(temp_paths)

    assert Path(result) == local_pythonw


def test_resolve_foreground_python_executable_requires_local_setup_when_checkout_venv_missing(
    monkeypatch,
    temp_paths,
) -> None:
    repo_root = temp_paths.user_profile
    _create_repo_checkout(repo_root)
    monkeypatch.setattr(
        "selfsnap.runtime_launch.resolve_source_repo_root",
        lambda _paths=None: str(repo_root),
    )

    with pytest.raises(RuntimeError, match="setup\\.ps1"):
        resolve_foreground_python_executable(temp_paths)


def test_resolve_source_repo_root_prefers_trusted_install_metadata(temp_paths) -> None:
    temp_paths.bin_dir.mkdir(parents=True, exist_ok=True)
    (temp_paths.bin_dir / "install-meta.json").write_text(
        '{"repo_root": "' + str(temp_paths.user_profile).replace("\\", "\\\\") + '"}',
        encoding="utf-8",
    )

    result = resolve_source_repo_root(temp_paths)

    assert Path(result) == temp_paths.user_profile


def test_read_install_metadata_returns_empty_dict_for_invalid_json(temp_paths) -> None:
    temp_paths.bin_dir.mkdir(parents=True, exist_ok=True)
    (temp_paths.bin_dir / "install-meta.json").write_text("{invalid", encoding="utf-8")

    assert read_install_metadata(temp_paths) == {}


def test_ensure_local_repository_interpreter_reexecutes_console_process_into_local_venv(
    monkeypatch, tmp_path
) -> None:
    repo_root = tmp_path / "repo"
    _create_repo_checkout(repo_root)
    local_python, _local_pythonw = _create_local_venv(repo_root)
    wrong_python = tmp_path / "global-python.exe"
    wrong_python.write_text("", encoding="utf-8")
    captured: dict[str, object] = {}

    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", str(wrong_python))
    monkeypatch.setattr("selfsnap.runtime_launch.sys.argv", [str(wrong_python), "doctor"])
    monkeypatch.setattr(
        "selfsnap.runtime_launch.resolve_source_repo_root",
        lambda _paths=None: str(repo_root),
    )

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=args[0], returncode=0)

    monkeypatch.setattr("selfsnap.runtime_launch.subprocess.run", fake_run)

    result = ensure_local_repository_interpreter(["doctor"])

    assert result == 0
    assert captured["args"] == ([str(local_python), "-m", "selfsnap", "doctor"],)
    kwargs = captured["kwargs"]
    assert kwargs["cwd"] == str(repo_root)
    assert kwargs["text"] is True
    assert kwargs["env"][INTERPRETER_REDIRECT_ENV] == "1"


def test_ensure_local_repository_interpreter_returns_none_when_already_using_local_venv(
    monkeypatch, tmp_path
) -> None:
    repo_root = tmp_path / "repo"
    _create_repo_checkout(repo_root)
    local_python, _local_pythonw = _create_local_venv(repo_root)

    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", str(local_python))
    monkeypatch.setattr(
        "selfsnap.runtime_launch.resolve_source_repo_root",
        lambda _paths=None: str(repo_root),
    )

    assert ensure_local_repository_interpreter(["doctor"]) is None


def test_ensure_local_repository_interpreter_reports_failed_redirect_loop(
    monkeypatch, tmp_path, capsys
) -> None:
    repo_root = tmp_path / "repo"
    _create_repo_checkout(repo_root)
    _create_local_venv(repo_root)
    wrong_python = tmp_path / "global-python.exe"
    wrong_python.write_text("", encoding="utf-8")

    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", str(wrong_python))
    monkeypatch.setattr(
        "selfsnap.runtime_launch.resolve_source_repo_root",
        lambda _paths=None: str(repo_root),
    )
    monkeypatch.setenv(INTERPRETER_REDIRECT_ENV, "1")

    result = ensure_local_repository_interpreter(["doctor"])

    assert result == 1
    assert "could not switch" in capsys.readouterr().err


def test_ensure_local_repository_interpreter_reexecutes_windowless_process_into_local_venv(
    monkeypatch, tmp_path
) -> None:
    repo_root = tmp_path / "repo"
    _create_repo_checkout(repo_root)
    _local_python, local_pythonw = _create_local_venv(repo_root)
    wrong_pythonw = tmp_path / "pythonw.exe"
    wrong_pythonw.write_text("", encoding="utf-8")
    captured: dict[str, object] = {}

    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", str(wrong_pythonw))
    monkeypatch.setattr("selfsnap.runtime_launch.sys.argv", [str(wrong_pythonw), "tray"])
    monkeypatch.setattr(
        "selfsnap.runtime_launch.resolve_source_repo_root",
        lambda _paths=None: str(repo_root),
    )

    def fake_popen(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("selfsnap.runtime_launch.subprocess.Popen", fake_popen)

    result = ensure_local_repository_interpreter(["tray"])

    assert result == 0
    assert captured["args"] == ([str(local_pythonw), "-m", "selfsnap", "tray"],)
    kwargs = captured["kwargs"]
    assert kwargs["cwd"] == str(repo_root)
    assert kwargs["text"] is True
    assert kwargs["env"][INTERPRETER_REDIRECT_ENV] == "1"


def test_ensure_local_repository_interpreter_reports_setup_when_checkout_venv_is_missing(
    monkeypatch, tmp_path, capsys
) -> None:
    repo_root = tmp_path / "repo"
    _create_repo_checkout(repo_root)
    wrong_python = tmp_path / "global-python.exe"
    wrong_python.write_text("", encoding="utf-8")

    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", str(wrong_python))
    monkeypatch.setattr(
        "selfsnap.runtime_launch.resolve_source_repo_root",
        lambda _paths=None: str(repo_root),
    )

    result = ensure_local_repository_interpreter(["doctor"])

    assert result == 1
    assert "setup.ps1" in capsys.readouterr().err


def test_resolve_foreground_python_executable_uses_python_sibling_for_pythonw_runtime(
    monkeypatch, tmp_path
) -> None:
    checkout_root = tmp_path / "not-a-checkout"
    checkout_root.mkdir(parents=True, exist_ok=True)
    pythonw = tmp_path / "pythonw.exe"
    python = tmp_path / "python.exe"
    pythonw.write_text("", encoding="utf-8")
    python.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        "selfsnap.runtime_launch.resolve_source_repo_root",
        lambda _paths=None: str(checkout_root),
    )
    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", str(pythonw))

    assert Path(resolve_foreground_python_executable()) == python


def test_resolve_foreground_python_executable_uses_existing_runtime_when_it_is_python(
    monkeypatch, tmp_path
) -> None:
    checkout_root = tmp_path / "not-a-checkout"
    checkout_root.mkdir(parents=True, exist_ok=True)
    python = tmp_path / "python.exe"
    python.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        "selfsnap.runtime_launch.resolve_source_repo_root",
        lambda _paths=None: str(checkout_root),
    )
    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", str(python))

    assert Path(resolve_foreground_python_executable()) == python


def test_resolve_background_python_executable_uses_existing_pythonw_runtime(
    monkeypatch, tmp_path
) -> None:
    checkout_root = tmp_path / "not-a-checkout"
    checkout_root.mkdir(parents=True, exist_ok=True)
    pythonw = tmp_path / "pythonw.exe"
    pythonw.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        "selfsnap.runtime_launch.resolve_source_repo_root",
        lambda _paths=None: str(checkout_root),
    )
    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", str(pythonw))

    assert Path(resolve_background_python_executable()) == pythonw


def test_resolve_tray_background_invocation_uses_frozen_executable(monkeypatch, temp_paths, tmp_path) -> None:
    executable = tmp_path / "SelfSnap.exe"
    executable.write_text("", encoding="utf-8")

    monkeypatch.setattr("selfsnap.runtime_launch.sys.frozen", True, raising=False)
    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", str(executable))

    spec = resolve_tray_background_invocation(temp_paths)

    assert spec.executable == str(executable)
    assert spec.arguments == []
    assert spec.working_directory == str(executable.parent)


def test_resolve_worker_background_invocation_uses_frozen_worker_binary(monkeypatch, temp_paths, tmp_path) -> None:
    executable = tmp_path / "SelfSnap.exe"
    worker = tmp_path / "SelfSnapWorker.exe"
    executable.write_text("", encoding="utf-8")
    worker.write_text("", encoding="utf-8")

    monkeypatch.setattr("selfsnap.runtime_launch.sys.frozen", True, raising=False)
    monkeypatch.setattr("selfsnap.runtime_launch.sys.executable", str(executable))

    spec = resolve_worker_background_invocation(
        temp_paths,
        "sched_1",
        "2026-03-01T09:00:00",
    )

    assert Path(spec.executable) == worker
    assert spec.arguments == [
        "capture",
        "--trigger",
        "scheduled",
        "--schedule-id",
        "sched_1",
        "--planned-local-ts",
        "2026-03-01T09:00:00",
    ]
    assert spec.working_directory == str(worker.parent)


def test_creation_flag_helpers_return_zero_off_windows(monkeypatch) -> None:
    monkeypatch.setattr("selfsnap.runtime_launch.sys.platform", "linux")

    assert _background_creation_flags() == 0
    assert _script_creation_flags() == 0


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


def test_launch_spec_argument_string_matches_subprocess_quoting(temp_paths) -> None:
    spec = LaunchSpec(
        executable="python.exe",
        arguments=["-m", "selfsnap", "capture", "--schedule-id", "sched 1"],
        working_directory=str(temp_paths.root),
    )

    assert spec.argument_string() == subprocess.list2cmdline(spec.arguments)


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
def test_run_helpers_request_text_mode(
    monkeypatch, temp_paths, runner_name, expected_stdio
) -> None:
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
