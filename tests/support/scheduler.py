from __future__ import annotations

from pathlib import Path

import selfsnap.scheduler.task_scheduler as task_scheduler
from selfsnap.runtime_launch import LaunchSpec


REPO_ROOT = Path(__file__).resolve().parents[2]


def fake_worker_background_invocation(
    _paths, schedule_id: str, planned_local_ts: str | None = None
) -> LaunchSpec:
    arguments = [
        "-m",
        "selfsnap",
        "capture",
        "--trigger",
        "scheduled",
        "--schedule-id",
        schedule_id,
    ]
    if planned_local_ts is not None:
        arguments.extend(["--planned-local-ts", planned_local_ts])
    return LaunchSpec(
        executable=str(REPO_ROOT / ".venv" / "Scripts" / "pythonw.exe"),
        arguments=arguments,
        working_directory=str(REPO_ROOT),
    )


def install_fake_worker_background_invocation(monkeypatch) -> None:
    monkeypatch.setattr(
        task_scheduler,
        "resolve_worker_background_invocation",
        fake_worker_background_invocation,
    )
