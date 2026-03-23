from __future__ import annotations

from pathlib import Path
import time

from selfsnap.paths import AppPaths
from selfsnap.runtime_launch import (
    LaunchSpec,
    launch_background,
    resolve_background_python_executable,
    resolve_foreground_python_executable,
    resolve_source_repo_root,
    resolve_tray_background_invocation,
)


def _require_script(repo_root: Path, relative_path: tuple[str, ...]) -> Path:
    script_path = repo_root.joinpath(*relative_path)
    if not script_path.exists():
        missing_path = str(script_path)
        raise RuntimeError(f"Required lifecycle script is missing: {missing_path}")
    return script_path


def resolve_restart_invocation(paths: AppPaths) -> LaunchSpec:
    return resolve_tray_background_invocation(paths)


def resolve_reinstall_invocation(
    paths: AppPaths,
    *,
    update_source: bool,
    relaunch_tray: bool = True,
) -> LaunchSpec:
    repo_root = Path(resolve_source_repo_root(paths))
    script_path = _require_script(repo_root, ("scripts", "reinstall.ps1"))
    arguments = [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-PythonExe",
        resolve_foreground_python_executable(paths),
        "-PythonwExe",
        resolve_background_python_executable(paths),
    ]
    if update_source:
        arguments.append("-UpdateSource")
    if relaunch_tray:
        arguments.append("-RelaunchTray")
    return LaunchSpec(
        executable="powershell.exe",
        arguments=arguments,
        working_directory=str(repo_root),
    )


def resolve_uninstall_invocation(paths: AppPaths, *, remove_user_data: bool) -> LaunchSpec:
    repo_root = Path(resolve_source_repo_root(paths))
    script_path = _require_script(repo_root, ("scripts", "uninstall.ps1"))
    arguments = [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-PythonExe",
        resolve_foreground_python_executable(paths),
    ]
    if remove_user_data:
        arguments.append("-RemoveUserData")
    return LaunchSpec(
        executable="powershell.exe",
        arguments=arguments,
        working_directory=str(repo_root),
    )


def launch_and_confirm(spec: LaunchSpec, *, wait_seconds: float = 2.0) -> bool:
    process = launch_background(spec)
    return _wait_for_process_start(process, wait_seconds=wait_seconds)


def _wait_for_process_start(process, *, wait_seconds: float) -> bool:
    poll = getattr(process, "poll", None)
    if poll is None:
        return True
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if poll() is not None:
            return False
        time.sleep(0.2)
    return poll() is None
