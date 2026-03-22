from __future__ import annotations

import csv
from datetime import date
import io
import json
import logging
import os
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.logging_setup import setup_logging
from selfsnap.models import AppConfig, OutcomeCode
from selfsnap.paths import AppPaths, resolve_app_paths
from selfsnap.runtime_launch import LaunchSpec, resolve_worker_background_invocation
from selfsnap.worker import EXIT_OK, EXIT_SCHEDULER_FAILURE


TASK_PREFIX = "SelfSnap.Capture."


def sync_scheduler_from_config(paths: AppPaths | None = None, emit_console: bool = True) -> int:
    paths = paths or resolve_app_paths()
    config = load_or_create_config(paths)
    logger = setup_logging(paths, config.log_level)
    try:
        sync_tasks(paths, config, logger)
        config.mark_scheduler_sync_ok()
        _persist_scheduler_sync_state(paths, config, logger)
        return EXIT_OK
    except Exception as exc:
        config.mark_scheduler_sync_failed(str(exc))
        _persist_scheduler_sync_state(paths, config, logger)
        logger.exception("Scheduler sync failed with %s", OutcomeCode.SCHEDULER_SYNC_ERROR.value)
        if emit_console:
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


def delete_all_selfsnap_tasks(logger: logging.Logger | None = None) -> list[str]:
    deleted: list[str] = []
    for task_name in list_selfsnap_tasks():
        delete_task(task_name, logger, ignore_missing=True)
        deleted.append(task_name)
    return deleted


def build_desired_tasks(paths: AppPaths, config: AppConfig) -> dict[str, dict[str, object]]:
    if not config.first_run_completed or not config.app_enabled:
        return {}
    desired: dict[str, dict[str, object]] = {}
    for schedule in config.schedules:
        if not schedule.enabled:
            continue
        invocation = resolve_worker_background_invocation(paths, schedule.schedule_id)
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
    invocation: LaunchSpec,
    wake_for_run: bool,
    logger: logging.Logger,
) -> None:
    delete_task(task_name, logger, ignore_missing=True)
    try:
        result = _register_task_with_powershell(task_name, time_value, invocation, wake_for_run)
    except RuntimeError as exc:
        logger.warning("Falling back to schtasks XML registration for %s: %s", task_name, exc)
        result = _register_task_with_xml(task_name, time_value, invocation, wake_for_run)
    logger.info("Created task %s at %s (wake=%s)", task_name, time_value, wake_for_run)
    if result.stdout:
        logger.debug("schtasks output: %s", result.stdout.strip())


def delete_task(
    task_name: str, logger: logging.Logger | None, ignore_missing: bool = False
) -> None:
    result = _run_schtasks(["/Delete", "/TN", task_name, "/F"], check=False)
    if result.returncode == 0:
        if logger is not None:
            logger.info("Deleted task %s", task_name)
        return
    combined = f"{result.stdout}\n{result.stderr}".lower()
    if ignore_missing and "cannot find" in combined:
        return
    raise RuntimeError(result.stderr or result.stdout or f"Failed to delete task {task_name}")


def build_task_action(paths: AppPaths, schedule_id: str) -> str:
    invocation = resolve_worker_background_invocation(paths, schedule_id)
    arguments = invocation.argument_string()
    if arguments:
        return f'"{invocation.executable}" {arguments}'
    return f'"{invocation.executable}"'


def resolve_worker_invocation(paths: AppPaths, schedule_id: str) -> LaunchSpec:
    return resolve_worker_background_invocation(paths, schedule_id)


def _register_task_with_powershell(
    task_name: str,
    time_value: str,
    invocation: LaunchSpec,
    wake_for_run: bool,
) -> subprocess.CompletedProcess[str]:
    current_user = _resolve_current_windows_user()
    script = f"""
$ErrorActionPreference = 'Stop'
$taskName = '{_escape_powershell_string(task_name)}'
$execute = '{_escape_powershell_string(invocation.executable)}'
$arguments = '{_escape_powershell_string(invocation.argument_string())}'
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


def _register_task_with_xml(
    task_name: str,
    time_value: str,
    invocation: LaunchSpec,
    wake_for_run: bool,
) -> subprocess.CompletedProcess[str]:
    task_xml = _build_task_xml(task_name, time_value, invocation, wake_for_run)
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".xml", encoding="utf-8") as handle:
        handle.write(task_xml)
        xml_path = Path(handle.name)
    try:
        result = _run_schtasks(["/Create", "/TN", task_name, "/XML", str(xml_path), "/F"])
        _verify_registered_task(task_name, invocation, wake_for_run)
        return result
    finally:
        xml_path.unlink(missing_ok=True)


def _build_task_xml(
    task_name: str,
    time_value: str,
    invocation: LaunchSpec,
    wake_for_run: bool,
) -> str:
    current_user = _resolve_current_windows_user()
    start_boundary = f"{date.today().isoformat()}T{time_value}:00"
    task = ET.Element(
        "Task",
        {
            "version": "1.4",
            "xmlns": "http://schemas.microsoft.com/windows/2004/02/mit/task",
        },
    )
    registration = ET.SubElement(task, "RegistrationInfo")
    ET.SubElement(registration, "Author").text = "SelfSnap"
    ET.SubElement(registration, "Description").text = f"{task_name} scheduled capture"

    triggers = ET.SubElement(task, "Triggers")
    calendar_trigger = ET.SubElement(triggers, "CalendarTrigger")
    ET.SubElement(calendar_trigger, "StartBoundary").text = start_boundary
    ET.SubElement(calendar_trigger, "Enabled").text = "true"
    schedule_by_day = ET.SubElement(calendar_trigger, "ScheduleByDay")
    ET.SubElement(schedule_by_day, "DaysInterval").text = "1"

    principals = ET.SubElement(task, "Principals")
    principal = ET.SubElement(principals, "Principal", {"id": "Author"})
    ET.SubElement(principal, "UserId").text = current_user
    ET.SubElement(principal, "LogonType").text = "InteractiveToken"
    ET.SubElement(principal, "RunLevel").text = "LeastPrivilege"

    settings = ET.SubElement(task, "Settings")
    ET.SubElement(settings, "MultipleInstancesPolicy").text = "IgnoreNew"
    ET.SubElement(settings, "DisallowStartIfOnBatteries").text = "false"
    ET.SubElement(settings, "StopIfGoingOnBatteries").text = "false"
    ET.SubElement(settings, "AllowHardTerminate").text = "true"
    ET.SubElement(settings, "StartWhenAvailable").text = "false"
    ET.SubElement(settings, "RunOnlyIfNetworkAvailable").text = "false"
    idle = ET.SubElement(settings, "IdleSettings")
    ET.SubElement(idle, "StopOnIdleEnd").text = "false"
    ET.SubElement(idle, "RestartOnIdle").text = "false"
    ET.SubElement(settings, "AllowStartOnDemand").text = "true"
    ET.SubElement(settings, "Enabled").text = "true"
    ET.SubElement(settings, "Hidden").text = "false"
    ET.SubElement(settings, "RunOnlyIfIdle").text = "false"
    ET.SubElement(settings, "WakeToRun").text = "true" if wake_for_run else "false"
    ET.SubElement(settings, "ExecutionTimeLimit").text = "PT1H"
    ET.SubElement(settings, "Priority").text = "7"

    actions = ET.SubElement(task, "Actions", {"Context": "Author"})
    exec_action = ET.SubElement(actions, "Exec")
    ET.SubElement(exec_action, "Command").text = invocation.executable
    ET.SubElement(exec_action, "Arguments").text = invocation.argument_string()
    ET.SubElement(exec_action, "WorkingDirectory").text = invocation.working_directory
    return ET.tostring(task, encoding="unicode", xml_declaration=True)


def _verify_registered_task(task_name: str, invocation: LaunchSpec, wake_for_run: bool) -> None:
    root = _query_task_xml(task_name)
    namespace = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
    command = root.findtext(".//t:Exec/t:Command", namespaces=namespace)
    arguments = root.findtext(".//t:Exec/t:Arguments", namespaces=namespace)
    working_directory = root.findtext(".//t:Exec/t:WorkingDirectory", namespaces=namespace)
    wake_to_run = root.findtext(".//t:Settings/t:WakeToRun", namespaces=namespace)
    if command != invocation.executable:
        raise RuntimeError("Registered task executable does not match requested value.")
    if (arguments or "") != invocation.argument_string():
        raise RuntimeError("Registered task arguments do not match requested value.")
    if (working_directory or "") != invocation.working_directory:
        raise RuntimeError("Registered task working directory does not match requested value.")
    if (wake_to_run or "").lower() != ("true" if wake_for_run else "false"):
        raise RuntimeError("Registered task wake setting does not match requested value.")


def _query_task_xml(task_name: str) -> ET.Element:
    result = _run_schtasks(["/Query", "/TN", task_name, "/XML"])
    return ET.fromstring(result.stdout)


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


def _persist_scheduler_sync_state(paths: AppPaths, config: AppConfig, logger: logging.Logger) -> None:
    try:
        save_config(paths, config)
    except Exception:
        logger.exception("Failed to persist scheduler sync state")


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

    payload = json.loads(result.stdout)
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return payload
    return []
