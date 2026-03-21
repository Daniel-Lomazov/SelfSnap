from __future__ import annotations

import csv
import io
import logging
import subprocess
import sys
from pathlib import Path

from selfsnap.config_store import load_or_create_config
from selfsnap.logging_setup import setup_logging
from selfsnap.models import OutcomeCode
from selfsnap.paths import AppPaths, resolve_app_paths
from selfsnap.worker import EXIT_SCHEDULER_FAILURE, EXIT_OK


TASK_PREFIX = "SelfSnap.Capture."


def sync_scheduler_from_config(paths: AppPaths | None = None) -> int:
    paths = paths or resolve_app_paths()
    config = load_or_create_config(paths)
    logger = setup_logging(paths, config.log_level)
    try:
        sync_tasks(paths, config.schedules, logger)
        return EXIT_OK
    except Exception as exc:
        logger.exception("Scheduler sync failed with %s", OutcomeCode.SCHEDULER_SYNC_ERROR.value)
        print(f"Scheduler sync failed: {exc}")
        return EXIT_SCHEDULER_FAILURE


def sync_tasks(paths: AppPaths, schedules: list, logger: logging.Logger) -> None:
    existing = list_selfsnap_tasks()
    desired = {f"{TASK_PREFIX}{schedule.schedule_id}": schedule for schedule in schedules}

    for task_name in existing - set(desired):
        delete_task(task_name, logger)

    for task_name, schedule in desired.items():
        create_or_replace_task(task_name, schedule.local_time, build_task_action(paths, schedule.schedule_id), logger)


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


def create_or_replace_task(task_name: str, time_value: str, action: str, logger: logging.Logger) -> None:
    delete_task(task_name, logger, ignore_missing=True)
    args = [
        "/Create",
        "/SC",
        "DAILY",
        "/TN",
        task_name,
        "/TR",
        action,
        "/ST",
        time_value,
        "/RL",
        "LIMITED",
        "/F",
    ]
    result = _run_schtasks(args)
    logger.info("Created task %s at %s", task_name, time_value)
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
    worker_command = resolve_worker_command(paths)
    return f'{worker_command} capture --trigger scheduled --schedule-id {schedule_id}'


def resolve_worker_command(paths: AppPaths) -> str:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable)
        if executable.name.lower() == "selfsnaptray.exe":
            worker_path = executable.with_name("SelfSnapWorker.exe")
        else:
            worker_path = executable
        return f'"{worker_path}"'

    python_executable = sys.executable
    if not python_executable:
        raise RuntimeError("Python executable path is unavailable for scheduler integration")
    return f'"{python_executable}" -m selfsnap'


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
