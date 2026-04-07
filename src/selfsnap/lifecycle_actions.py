from __future__ import annotations

from pathlib import Path

from selfsnap.paths import AppPaths
from selfsnap.runtime_launch import (
    LaunchSpec,
    launch_background,
    launch_hidden_background,
    resolve_background_python_executable,
    resolve_foreground_python_executable,
    resolve_source_repo_root,
    resolve_tray_background_invocation,
    run_lifecycle_script,
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
    target_tag: str | None = None,
    relaunch_tray: bool = True,
) -> LaunchSpec:
    repo_root = Path(resolve_source_repo_root(paths))
    script_path = _require_script(repo_root, ("scripts", "reinstall.ps1"))
    arguments = [
        "-WindowStyle", "Hidden",
        "-NonInteractive",
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
    if target_tag:
        arguments += ["-TargetTag", target_tag]
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
        "-WindowStyle", "Hidden",
        "-NonInteractive",
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


def _powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _powershell_argument_list(arguments: list[str]) -> str:
    if not arguments:
        return "@()"
    quoted = ", ".join(_powershell_quote(argument) for argument in arguments)
    return f"@({quoted})"


def resolve_tray_relaunch_after_exit_invocation(
    paths: AppPaths,
    *,
    wait_for_process_id: int,
) -> LaunchSpec:
    tray_spec = resolve_tray_background_invocation(paths)
    command = (
        "$ErrorActionPreference = 'Stop'; "
        f"Wait-Process -Id {wait_for_process_id} -ErrorAction SilentlyContinue; "
        f"Start-Process -FilePath {_powershell_quote(tray_spec.executable)} "
        f"-ArgumentList {_powershell_argument_list(tray_spec.arguments)} "
        f"-WorkingDirectory {_powershell_quote(tray_spec.working_directory)} "
        "-WindowStyle Hidden"
    )
    return LaunchSpec(
        executable="powershell.exe",
        arguments=[
            "-WindowStyle",
            "Hidden",
            "-NonInteractive",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        working_directory=tray_spec.working_directory,
    )


def schedule_tray_relaunch_after_exit(paths: AppPaths, *, wait_for_process_id: int) -> bool:
    process = launch_hidden_background(
        resolve_tray_relaunch_after_exit_invocation(
            paths,
            wait_for_process_id=wait_for_process_id,
        )
    )
    poll = getattr(process, "poll", None)
    if poll is None:
        return True
    return poll() is None


def launch_and_confirm(spec: LaunchSpec, *, wait_seconds: float = 2.0) -> bool:
    """Launch a background process (pythonw.exe) and verify it stays alive briefly.

    Only use for non-console background processes (e.g. restart). For PowerShell
    lifecycle scripts use run_lifecycle_script_and_check instead.
    """
    import time
    process = launch_background(spec)
    poll = getattr(process, "poll", None)
    if poll is None:
        return True
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if poll() is not None:
            return False
        time.sleep(0.2)
    return poll() is None


def run_lifecycle_script_and_check(spec: LaunchSpec) -> bool:
    """Run a PowerShell lifecycle script synchronously and return True on exit code 0.

    This is the single uniform pattern for all lifecycle scripts (reinstall,
    check-for-updates, uninstall). Running synchronously means:
    - No liveness-window race conditions (fast success != launch failure)
    - Exit code is ground truth (scripts use $ErrorActionPreference=Stop)
    - The tray thread blocks while the script runs, which is acceptable since
      the tray exits immediately after on success anyway
    """
    result = run_lifecycle_script(spec)
    return result.returncode == 0
