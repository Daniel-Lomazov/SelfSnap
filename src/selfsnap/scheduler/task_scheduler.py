from __future__ import annotations

import csv
from dataclasses import dataclass
import io
import logging
import os
import subprocess
import sys
from pathlib import Path

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.logging_setup import setup_logging
from selfsnap.models import AppConfig
from selfsnap.models import OutcomeCode
from selfsnap.paths import AppPaths, resolve_app_paths
from selfsnap.worker import EXIT_SCHEDULER_FAILURE, EXIT_OK


TASK_PREFIX = "SelfSnap.Capture."


@dataclass(slots=True)
class TaskInvocation:
    executable: str
    arguments: str
    working_directory: str


def sync_scheduler_from_config(paths: AppPaths | None = None) -> int:
    paths = paths or resolve_app_paths()
    config = load_or_create_config(paths)
    logger = setup_logging(paths, config.log_level)
    try:
        sync_tasks(paths, config, logger)
        config.mark_scheduler_sync_ok()
        save_config(paths, config)
        return EXIT_OK
    except Exception as exc:
        config.mark_scheduler_sync_failed(str(exc))
        save_config(paths, config)
        logger.exception("Scheduler sync failed with %s", OutcomeCode.SCHEDULER_SYNC_ERROR.value)
        print(f"Scheduler sync failed: {exc}")
        return EXIT_SCHEDULER_FAILURE


def sync_tasks(paths: AppPaths, config: AppConfig, logger: logging.Logger) -> None:
    existing = list_selfsnap_tasks()
    desired = build_desired_tasks(paths, config)

    for task_name in existing - set(desired):
        delete_task(task_name, logger)

    for task_name, task_spec in desired.items():
        create_or_replace_task(
            task_name,
            task_spec["time_value"],
            task_spec["invocation"],
            bool(task_spec["wake"]),
            logger,
        )


def build_desired_tasks(paths: AppPaths, config: AppConfig) -> dict[str, dict[str, object]]:
    if not config.first_run_completed or not config.app_enabled:
        return {}
    desired: dict[str, dict[str, object]] = {}
    for schedule in config.schedules:
        if not schedule.enabled:
            continue
        invocation = resolve_worker_invocation(paths, schedule.schedule_id)
        desired[f"{TASK_PREFIX}{schedule.schedule_id}"] = {
            "time_value": schedule.local_time,
            "invocation": invocation,
            "wake": config.wake_for_scheduled_captures,
        }
    return desired


def list_selfsnap_tasks() -> set[str]:
    result = _run_schtasks(["/Query", "/FO", "CSV", "/NH"], check=False)
    if result.returncode != 0:
        return set()
    reader = csv.reader(io.StringIO(result.stdout))
    names: set[str] = set()
    for row in reader:
        if not row:
            continue
        task_name = row[0].lstrip("\\")
        if task_name.startswith(TASK_PREFIX):
            names.add(task_name)
    return names


def create_or_replace_task(
    task_name: str,
    time_value: str,
    invocation: TaskInvocation,
    wake_for_run: bool,
    logger: logging.Logger,
) -> None:
    delete_task(task_name, logger, ignore_missing=True)
    result = _register_task_with_powershell(task_name, time_value, invocation, wake_for_run)
    logger.info("Created task %s at %s (wake=%s)", task_name, time_value, wake_for_run)
    if result.stdout:
        logger.debug("schtasks output: %s", result.stdout.strip())


def delete_task(task_name: str, logger: logging.Logger, ignore_missing: bool = False) -> None:
    result = _run_schtasks(["/Delete", "/TN", task_name, "/F"], check=False)
    if result.returncode == 0:
        logger.info("Deleted task %s", task_name)
        return
    combined = f"{result.stdout}\n{result.stderr}".lower()
    if ignore_missing and "cannot find" in combined:
        return
    raise RuntimeError(result.stderr or result.stdout or f"Failed to delete task {task_name}")


def build_task_action(paths: AppPaths, schedule_id: str) -> str:
    invocation = resolve_worker_invocation(paths, schedule_id)
    if invocation.arguments:
        return f'"{invocation.executable}" {invocation.arguments}'
    return f'"{invocation.executable}"'


def resolve_worker_invocation(paths: AppPaths, schedule_id: str) -> TaskInvocation:
    wrapper_path = paths.bin_dir / "SelfSnap.cmd"
    if wrapper_path.exists():
        cmd_executable = os.environ.get("ComSpec", r"C:\Windows\System32\cmd.exe")
        return TaskInvocation(
            executable=cmd_executable,
            arguments=f'/d /c ""{wrapper_path}" capture --trigger scheduled --schedule-id {schedule_id}""',
            working_directory=str(paths.root),
        )
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable)
        if executable.name.lower() == "selfsnaptray.exe":
            worker_path = executable.with_name("SelfSnapWorker.exe")
        else:
            worker_path = executable
        return TaskInvocation(
            executable=str(worker_path),
            arguments=f"capture --trigger scheduled --schedule-id {schedule_id}",
            working_directory=str(worker_path.parent),
        )

    python_executable = sys.executable
    if not python_executable:
        raise RuntimeError("Python executable path is unavailable for scheduler integration")
    return TaskInvocation(
        executable=python_executable,
        arguments=f"-m selfsnap capture --trigger scheduled --schedule-id {schedule_id}",
        working_directory=str(paths.root),
    )


def _register_task_with_powershell(
    task_name: str,
    time_value: str,
    invocation: TaskInvocation,
    wake_for_run: bool,
) -> subprocess.CompletedProcess[str]:
    current_user = _resolve_current_windows_user()
    script = f"""
$ErrorActionPreference = 'Stop'
$taskName = '{_escape_powershell_string(task_name)}'
$execute = '{_escape_powershell_string(invocation.executable)}'
$arguments = '{_escape_powershell_string(invocation.arguments)}'
$workingDirectory = '{_escape_powershell_string(invocation.working_directory)}'
$timeValue = '{_escape_powershell_string(time_value)}'
$userId = '{_escape_powershell_string(current_user)}'
$wake = {'$true' if wake_for_run else '$false'}
$action = New-ScheduledTaskAction -Execute $execute -Argument $arguments -WorkingDirectory $workingDirectory
$trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::ParseExact($timeValue, 'HH:mm', $null))
$settings = New-ScheduledTaskSettingsSet -WakeToRun:$wake -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal
Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null
$registeredTask = Get-ScheduledTask -TaskName $taskName
if ($registeredTask.Settings.WakeToRun -ne $wake) {{
    throw "Registered task wake setting does not match requested value."
}}
$registeredAction = $registeredTask.Actions | Select-Object -First 1
if ($registeredAction.Execute -ne $execute) {{
    throw "Registered task executable does not match requested value."
}}
if ($registeredAction.Arguments -ne $arguments) {{
    throw "Registered task arguments do not match requested value."
}}
"""
    return _run_powershell(script)


def _resolve_current_windows_user() -> str:
    domain = os.environ.get("USERDOMAIN", "")
    username = os.environ.get("USERNAME", "")
    if username and domain:
        return f"{domain}\\{username}"
    if username:
        return username
    raise RuntimeError("Unable to resolve the current Windows user for task registration")


def _escape_powershell_string(value: str) -> str:
    return value.replace("'", "''")


def _run_powershell(command: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout or "PowerShell task registration failed")
    return completed


def _run_schtasks(arguments: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["schtasks", *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout or "schtasks failed")
    return completed


def read_registered_task_details() -> list[dict[str, object]]:
    script = f"""
$tasks = Get-ScheduledTask | Where-Object {{ $_.TaskName -like '{TASK_PREFIX}*' }} | ForEach-Object {{
    $action = $_.Actions | Select-Object -First 1
    [PSCustomObject]@{{
        task_name = $_.TaskName
        task_path = $_.TaskPath
        wake_to_run = $_.Settings.WakeToRun
        execute = $action.Execute
        arguments = $action.Arguments
        state = [string]$_.State
    }}
}}
$tasks | ConvertTo-Json -Depth 3
"""
    result = _run_powershell(script, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    import json

    payload = json.loads(result.stdout)
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return payload
    return []
