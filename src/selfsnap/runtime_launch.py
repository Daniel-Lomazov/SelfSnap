from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
import sys
from pathlib import Path

from selfsnap.paths import AppPaths


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


def resolve_foreground_python_executable(paths: AppPaths | None = None) -> str:
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
        "Foreground launch requires python.exe. Re-run scripts/setup.ps1 and scripts/install.ps1 "
        "with a standard Windows Python installation."
    )


def resolve_background_python_executable(paths: AppPaths | None = None) -> str:
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
        "Background launch requires pythonw.exe. Re-run scripts/setup.ps1 and scripts/install.ps1 "
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
    )


def run_background_command(spec: LaunchSpec) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        spec.command(),
        cwd=spec.working_directory,
        creationflags=_background_creation_flags(),
        check=False,
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
    )
