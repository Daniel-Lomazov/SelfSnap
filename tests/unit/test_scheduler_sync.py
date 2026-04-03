from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.models import Schedule
from selfsnap.scheduler.task_scheduler import (
    _build_task_xml,
    build_desired_tasks,
    build_task_action,
    resolve_worker_invocation,
)


def test_build_task_action_includes_schedule_id(temp_paths) -> None:
    action = build_task_action(temp_paths, "afternoon")
    assert "capture --trigger scheduled --schedule-id afternoon" in action


def test_build_desired_tasks_returns_empty_when_app_is_disabled(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = False
    config.schedules = [
        Schedule(
            schedule_id="afternoon",
            label="Afternoon",
            interval_value=1,
            interval_unit="day",
            start_date_local="2026-03-23",
            start_time_local="14:00:00",
        )
    ]
    save_config(temp_paths, config)

    assert build_desired_tasks(temp_paths, config) == {}


def test_build_desired_tasks_includes_enabled_schedules(temp_paths) -> None:
    local_tz = datetime.now().astimezone().tzinfo
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.wake_for_scheduled_captures = True
    config.schedules = [
        Schedule(
            schedule_id="morning",
            label="Morning",
            interval_value=1,
            interval_unit="day",
            start_date_local="2026-03-23",
            start_time_local="09:00:00",
            enabled=True,
        ),
        Schedule(
            schedule_id="off",
            label="Off",
            interval_value=1,
            interval_unit="day",
            start_date_local="2026-03-23",
            start_time_local="10:00:00",
            enabled=False,
        ),
    ]

    desired = build_desired_tasks(
        temp_paths,
        config,
        now_local=datetime(2026, 3, 23, 8, 0, 0, tzinfo=local_tz),
    )

    assert set(desired) == {"SelfSnap.Capture.morning"}
    run_at_local = desired["SelfSnap.Capture.morning"]["run_at_local"]
    assert isinstance(run_at_local, datetime)
    assert run_at_local.date().isoformat() == "2026-03-23"
    assert run_at_local.time().isoformat() == "09:00:00"
    assert desired["SelfSnap.Capture.morning"]["wake"] is True
    invocation = desired["SelfSnap.Capture.morning"]["invocation"]
    assert invocation.arguments == [
        "-m",
        "selfsnap",
        "capture",
        "--trigger",
        "scheduled",
        "--schedule-id",
        "morning",
        "--planned-local-ts",
        run_at_local.isoformat(),
    ]
    assert (Path(invocation.working_directory) / "pyproject.toml").exists()


def test_build_desired_tasks_still_returns_tasks_while_sync_state_is_failed(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.mark_scheduler_sync_failed("previous sync failure")
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

    desired = build_desired_tasks(temp_paths, config)

    assert set(desired) == {"SelfSnap.Capture.morning"}


def test_resolve_worker_invocation_uses_background_python(temp_paths) -> None:
    invocation = resolve_worker_invocation(temp_paths, "morning")

    assert invocation.executable.lower().endswith(("pythonw.exe", "selfsnapworker.exe"))
    assert invocation.arguments[-2:] == ["--schedule-id", "morning"]


def test_build_task_xml_preserves_wake_and_exec_settings(temp_paths) -> None:
    invocation = resolve_worker_invocation(temp_paths, "morning")

    xml_payload = _build_task_xml(
        "SelfSnap.Capture.morning",
        datetime(2026, 3, 23, 9, 0, 0, tzinfo=UTC),
        invocation,
        True,
    )
    root = ET.fromstring(xml_payload)
    namespace = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}

    assert root.findtext(".//t:Exec/t:Command", namespaces=namespace) == invocation.executable
    assert (
        root.findtext(".//t:Exec/t:Arguments", namespaces=namespace) == invocation.argument_string()
    )
    assert (
        root.findtext(".//t:Exec/t:WorkingDirectory", namespaces=namespace)
        == invocation.working_directory
    )
    assert root.findtext(".//t:Settings/t:WakeToRun", namespaces=namespace) == "true"
