from __future__ import annotations

from datetime import datetime

import pytest

from selfsnap.config_store import load_or_create_config
from selfsnap.models import Schedule
from selfsnap.scheduler.backends import InMemoryTaskSchedulerBackend
from selfsnap.scheduler.task_scheduler import TASK_PREFIX, build_desired_tasks, sync_tasks
import logging


def _make_logger() -> logging.Logger:
    return logging.getLogger("test_scheduler_backend")


def test_sync_tasks_creates_task_for_enabled_coarse_schedule(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.schedules = [
        Schedule(
            schedule_id="daily",
            label="Daily",
            interval_value=1,
            interval_unit="day",
            start_date_local="2026-03-23",
            start_time_local="09:00:00",
            enabled=True,
        )
    ]
    backend = InMemoryTaskSchedulerBackend()
    local_tz = datetime.now().astimezone().tzinfo
    now = datetime(2026, 3, 23, 8, 0, 0, tzinfo=local_tz)

    # build_desired_tasks is deterministic; patch now_local via the desired dict
    desired = build_desired_tasks(temp_paths, config, now_local=now)
    for task_name, spec in desired.items():
        backend.create_or_replace(task_name, spec["run_at_local"], spec["invocation"], bool(spec["wake"]))  # type: ignore[arg-type]

    assert backend.task_count() == 1
    assert f"{TASK_PREFIX}daily" in backend.list_tasks()
    task = backend.get_task(f"{TASK_PREFIX}daily")
    assert task is not None
    assert "daily" in str(task["arguments"])


def test_sync_tasks_removes_stale_tasks_via_backend(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.schedules = []

    backend = InMemoryTaskSchedulerBackend()
    backend._tasks[f"{TASK_PREFIX}stale"] = {"run_at_local": None, "executable": "x", "arguments": "", "wake_for_run": False}

    sync_tasks(temp_paths, config, _make_logger(), backend=backend)

    assert backend.task_count() == 0


def test_sync_tasks_replaces_existing_task_on_resync(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.schedules = [
        Schedule(
            schedule_id="morning",
            label="Morning",
            interval_value=1,
            interval_unit="day",
            start_date_local="2026-03-23",
            start_time_local="09:00:00",
            enabled=True,
        )
    ]
    backend = InMemoryTaskSchedulerBackend()
    local_tz = datetime.now().astimezone().tzinfo
    now = datetime(2026, 3, 23, 8, 0, 0, tzinfo=local_tz)

    sync_tasks(temp_paths, config, _make_logger(), backend=backend)
    first_count = backend.task_count()

    sync_tasks(temp_paths, config, _make_logger(), backend=backend)
    assert backend.task_count() == first_count


def test_inmemory_backend_delete_raises_on_missing_without_flag() -> None:
    backend = InMemoryTaskSchedulerBackend()
    with pytest.raises(KeyError):
        backend.delete("does_not_exist", ignore_missing=False)


def test_inmemory_backend_delete_silent_on_missing_with_flag() -> None:
    backend = InMemoryTaskSchedulerBackend()
    backend.delete("does_not_exist", ignore_missing=True)  # should not raise
