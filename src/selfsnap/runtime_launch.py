from __future__ import annotations

from dataclasses import dataclass
import json
import os
import subprocess
import sys
from pathlib import Path

from selfsnap.paths import AppPaths


LOCAL_VENV_DIRNAME = ".venv"
INTERPRETER_REDIRECT_ENV = "SELFSNAP_INTERPRETER_REDIRECTED"


@dataclass(slots=True)
class LaunchSpec:
    executable: str
    arguments: list[str]
    working_directory: str

    def command(self) -> list[str]:
        return [self.executable, *self.arguments]

    def argument_string(self) -> str:
        return subprocess.list2cmdline(self.arguments)


def read_install_metadata(paths: AppPaths) -> dict[str, object]:
    meta_path = paths.bin_dir / "install-meta.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _resolve_metadata_repo_root(paths: AppPaths | None = None) -> Path | None:
    if paths is None:
        return None
    metadata = read_install_metadata(paths)
    repo_root = metadata.get("repo_root")
    if isinstance(repo_root, str) and repo_root:
        candidate = Path(repo_root)
        if candidate.exists():
            return candidate
    return None


def resolve_source_repo_root(paths: AppPaths | None = None) -> str:
    metadata_repo_root = _resolve_metadata_repo_root(paths)
    if metadata_repo_root is not None:
        return str(metadata_repo_root)

    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / "pyproject.toml").exists():
        return str(repo_root)

    if paths is not None:
        return str(paths.root)
    return str(repo_root)


def _resolve_checkout_repo_root(paths: AppPaths | None = None) -> Path | None:
    repo_root = Path(resolve_source_repo_root(paths))
    if not (repo_root / "pyproject.toml").exists():
        return None
    if not (repo_root / "scripts" / "user" / "setup.ps1").exists():
        return None
    return repo_root


def _resolve_local_venv_python_executable(
    paths: AppPaths | None = None,
    *,
    windowless: bool,
) -> Path | None:
    repo_root = _resolve_checkout_repo_root(paths)
    if repo_root is None:
        return None
    executable = repo_root / LOCAL_VENV_DIRNAME / "Scripts" / (
        "pythonw.exe" if windowless else "python.exe"
    )
    if executable.exists():
        return executable
    return None


def _local_venv_setup_message(paths: AppPaths | None = None) -> str:
    repo_root = _resolve_checkout_repo_root(paths)
    if repo_root is None:
        return "Run .\\scripts\\user\\setup.ps1 from the repository root and retry."
    setup_script = repo_root / "scripts" / "user" / "setup.ps1"
    venv_root = repo_root / LOCAL_VENV_DIRNAME
    return (
        f"SelfSnap requires the repository-local virtual environment at {venv_root}. "
        f"Run {setup_script} and retry."
    )


def _require_local_venv_python_executable(
    paths: AppPaths | None = None,
    *,
    windowless: bool,
) -> str | None:
    executable = _resolve_local_venv_python_executable(paths, windowless=windowless)
    if executable is not None:
        return str(executable)
    if _resolve_checkout_repo_root(paths) is not None:
        raise RuntimeError(_local_venv_setup_message(paths))
    return None


def _normalized_executable_path(value: str | Path) -> str:
    return os.path.normcase(str(Path(value).resolve(strict=False)))


def ensure_local_repository_interpreter(
    argv: list[str] | None = None,
    *,
    paths: AppPaths | None = None,
) -> int | None:
    if getattr(sys, "frozen", False):
        return None

    repo_root = _resolve_checkout_repo_root(paths)
    if repo_root is None:
        return None

    current_executable = Path(sys.executable)
    windowless = current_executable.name.lower() == "pythonw.exe"
    expected_executable = _resolve_local_venv_python_executable(paths, windowless=windowless)
    if expected_executable is None:
        print(_local_venv_setup_message(paths), file=sys.stderr)
        return 1

    if _normalized_executable_path(current_executable) == _normalized_executable_path(
        expected_executable
    ):
        return None

    if os.environ.get(INTERPRETER_REDIRECT_ENV) == "1":
        print(
            f"SelfSnap could not switch to the repository-local interpreter {expected_executable}.",
            file=sys.stderr,
        )
        return 1

    redirected_argv = list(sys.argv[1:] if argv is None else argv)
    command = [str(expected_executable), "-m", "selfsnap", *redirected_argv]
    environment = os.environ.copy()
    environment[INTERPRETER_REDIRECT_ENV] = "1"

    if windowless:
        subprocess.Popen(
            command,
            cwd=str(repo_root),
            env=environment,
            creationflags=_background_creation_flags(),
            close_fds=False,
            text=True,
        )
        return 0

    completed = subprocess.run(
        command,
        cwd=str(repo_root),
        env=environment,
        check=False,
        text=True,
    )
    return int(completed.returncode)


def resolve_foreground_python_executable(paths: AppPaths | None = None) -> str:
    local_executable = _require_local_venv_python_executable(paths, windowless=False)
    if local_executable is not None:
        return local_executable

    metadata_repo_root = _resolve_metadata_repo_root(paths)
    if paths is not None and metadata_repo_root is not None:
        metadata = read_install_metadata(paths)
        python_executable = metadata.get("python_executable")
        if isinstance(python_executable, str) and Path(python_executable).exists():
            return python_executable

    executable = Path(sys.executable)
    if executable.name.lower() == "pythonw.exe":
        python_executable = executable.with_name("python.exe")
        if python_executable.exists():
            return str(python_executable)
    if executable.exists():
        return str(executable)
    raise RuntimeError(
        "Foreground launch requires python.exe. Re-run scripts/user/setup.ps1 and scripts/user/install.ps1 "
        "with a standard Windows Python installation."
    )


def resolve_background_python_executable(paths: AppPaths | None = None) -> str:
    local_executable = _require_local_venv_python_executable(paths, windowless=True)
    if local_executable is not None:
        return local_executable

    if paths is not None:
        metadata = read_install_metadata(paths)
        pythonw_executable = metadata.get("pythonw_executable")
        python_executable = metadata.get("python_executable")
        repo_root_valid = _resolve_metadata_repo_root(paths) is not None
        if (
            repo_root_valid
            and isinstance(pythonw_executable, str)
            and Path(pythonw_executable).exists()
        ):
            return pythonw_executable
        if repo_root_valid and isinstance(python_executable, str):
            metadata_python = Path(python_executable)
            metadata_pythonw = metadata_python.with_name("pythonw.exe")
            if metadata_python.exists() and metadata_pythonw.exists():
                return str(metadata_pythonw)

    executable = Path(sys.executable)
    if executable.name.lower() == "pythonw.exe":
        return str(executable)
    pythonw = executable.with_name("pythonw.exe")
    if pythonw.exists():
        return str(pythonw)
    raise RuntimeError(
        "Background launch requires pythonw.exe. Re-run scripts/user/setup.ps1 and scripts/user/install.ps1 "
        "with a standard Windows Python installation."
    )


def resolve_background_working_directory(paths: AppPaths) -> str:
    return resolve_source_repo_root(paths)


def resolve_tray_background_invocation(paths: AppPaths) -> LaunchSpec:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable)
        return LaunchSpec(
            executable=str(executable),
            arguments=[],
            working_directory=str(executable.parent),
        )
    return LaunchSpec(
        executable=resolve_background_python_executable(paths),
        arguments=["-m", "selfsnap", "tray"],
        working_directory=resolve_background_working_directory(paths),
    )


def resolve_manual_capture_background_invocation(paths: AppPaths) -> LaunchSpec:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable)
        worker_path = executable.with_name("SelfSnapWorker.exe")
        return LaunchSpec(
            executable=str(worker_path),
            arguments=["capture", "--trigger", "manual"],
            working_directory=str(worker_path.parent),
        )
    return LaunchSpec(
        executable=resolve_background_python_executable(paths),
        arguments=["-m", "selfsnap", "capture", "--trigger", "manual"],
        working_directory=resolve_background_working_directory(paths),
    )


def resolve_worker_background_invocation(
    paths: AppPaths,
    schedule_id: str,
    planned_local_ts: str | None = None,
) -> LaunchSpec:
    scheduled_arguments = ["capture", "--trigger", "scheduled", "--schedule-id", schedule_id]
    module_arguments = ["-m", "selfsnap", "capture", "--trigger", "scheduled", "--schedule-id", schedule_id]
    if planned_local_ts:
        scheduled_arguments.extend(["--planned-local-ts", planned_local_ts])
        module_arguments.extend(["--planned-local-ts", planned_local_ts])
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable)
        worker_path = executable.with_name("SelfSnapWorker.exe")
        return LaunchSpec(
            executable=str(worker_path),
            arguments=scheduled_arguments,
            working_directory=str(worker_path.parent),
        )
    return LaunchSpec(
        executable=resolve_background_python_executable(paths),
        arguments=module_arguments,
        working_directory=resolve_background_working_directory(paths),
    )


def _background_creation_flags() -> int:
    if sys.platform != "win32":
        return 0
    return (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "DETACHED_PROCESS", 0)
        | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )


def _script_creation_flags() -> int:
    """Flags for console-app lifecycle scripts (powershell).

    Intentionally omits DETACHED_PROCESS: powershell.exe launched with
    DETACHED_PROCESS from a windowless pythonw parent gets no I/O handles
    and exits immediately, causing the tray to falsely report failure.
    CREATE_NO_WINDOW suppresses the window without fully detaching.
    """
    if sys.platform != "win32":
        return 0
    return (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )


def launch_background(spec: LaunchSpec) -> subprocess.Popen[str]:
    return subprocess.Popen(
        spec.command(),
        cwd=spec.working_directory,
        creationflags=_background_creation_flags(),
        close_fds=False,
        text=True,
    )


def launch_hidden_background(spec: LaunchSpec) -> subprocess.Popen[str]:
    """Launch a helper PowerShell/script process without creating a visible window."""
    return subprocess.Popen(
        spec.command(),
        cwd=spec.working_directory,
        creationflags=_script_creation_flags(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        text=True,
        close_fds=False,
    )


def run_background_command(spec: LaunchSpec) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        spec.command(),
        cwd=spec.working_directory,
        creationflags=_background_creation_flags(),
        check=False,
        text=True,
    )


def run_lifecycle_script(spec: LaunchSpec) -> subprocess.CompletedProcess[str]:
    """Run a lifecycle PowerShell script synchronously and wait for completion."""
    return subprocess.run(
        spec.command(),
        cwd=spec.working_directory,
        creationflags=_script_creation_flags(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        check=False,
        text=True,
    )
