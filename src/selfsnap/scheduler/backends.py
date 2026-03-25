from __future__ import annotations

from datetime import datetime
from typing import Protocol

from selfsnap.runtime_launch import LaunchSpec


class TaskSchedulerBackend(Protocol):
    """Protocol for Windows Task Scheduler operations."""

    def list_tasks(self) -> set[str]:
        """Return the set of SelfSnap task names currently registered."""
        ...

    def create_or_replace(
        self,
        task_name: str,
        run_at_local: datetime,
        invocation: LaunchSpec,
        wake_for_run: bool,
    ) -> None:
        """Register (or replace) a scheduled task."""
        ...

    def delete(self, task_name: str, ignore_missing: bool = False) -> None:
        """Delete a scheduled task by name."""
        ...


class InMemoryTaskSchedulerBackend:
    """In-memory backend for use in tests — no Windows APIs required."""

    def __init__(self) -> None:
        self._tasks: dict[str, dict[str, object]] = {}

    def list_tasks(self) -> set[str]:
        return set(self._tasks.keys())

    def create_or_replace(
        self,
        task_name: str,
        run_at_local: datetime,
        invocation: LaunchSpec,
        wake_for_run: bool,
    ) -> None:
        self._tasks[task_name] = {
            "run_at_local": run_at_local,
            "executable": invocation.executable,
            "arguments": invocation.argument_string(),
            "wake_for_run": wake_for_run,
        }

    def delete(self, task_name: str, ignore_missing: bool = False) -> None:
        if task_name not in self._tasks:
            if not ignore_missing:
                raise KeyError(f"Task not found: {task_name}")
            return
        del self._tasks[task_name]

    def get_task(self, task_name: str) -> dict[str, object] | None:
        """Test helper: retrieve stored task details."""
        return self._tasks.get(task_name)

    def task_count(self) -> int:
        """Test helper: return number of registered tasks."""
        return len(self._tasks)
