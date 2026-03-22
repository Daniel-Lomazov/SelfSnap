from __future__ import annotations

import xml.etree.ElementTree as ET

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
    config.schedules = [Schedule(schedule_id="afternoon", label="Afternoon", local_time="14:00")]
    save_config(temp_paths, config)

    assert build_desired_tasks(temp_paths, config) == {}


def test_build_desired_tasks_includes_enabled_schedules(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.wake_for_scheduled_captures = True
    config.schedules = [
        Schedule(schedule_id="morning", label="Morning", local_time="09:00", enabled=True),
        Schedule(schedule_id="off", label="Off", local_time="10:00", enabled=False),
    ]

    desired = build_desired_tasks(temp_paths, config)

    assert set(desired) == {"SelfSnap.Capture.morning"}
    assert desired["SelfSnap.Capture.morning"]["time_value"] == "09:00"
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
    ]
    assert invocation.working_directory == str(temp_paths.root)


def test_build_desired_tasks_still_returns_tasks_while_sync_state_is_failed(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.mark_scheduler_sync_failed("previous sync failure")
    config.schedules = [Schedule(schedule_id="morning", label="Morning", local_time="09:00", enabled=True)]

    desired = build_desired_tasks(temp_paths, config)

    assert set(desired) == {"SelfSnap.Capture.morning"}


def test_resolve_worker_invocation_uses_background_python(temp_paths) -> None:
    invocation = resolve_worker_invocation(temp_paths, "morning")

    assert invocation.executable.lower().endswith(("pythonw.exe", "selfsnapworker.exe"))
    assert invocation.arguments[-2:] == ["--schedule-id", "morning"]


def test_build_task_xml_preserves_wake_and_exec_settings(temp_paths) -> None:
    invocation = resolve_worker_invocation(temp_paths, "morning")

    xml_payload = _build_task_xml("SelfSnap.Capture.morning", "09:00", invocation, True)
    root = ET.fromstring(xml_payload)
    namespace = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}

    assert root.findtext(".//t:Exec/t:Command", namespaces=namespace) == invocation.executable
    assert root.findtext(".//t:Exec/t:Arguments", namespaces=namespace) == invocation.argument_string()
    assert root.findtext(".//t:Exec/t:WorkingDirectory", namespaces=namespace) == invocation.working_directory
    assert root.findtext(".//t:Settings/t:WakeToRun", namespaces=namespace) == "true"
