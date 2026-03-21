from __future__ import annotations

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.models import Schedule
from selfsnap.scheduler.task_scheduler import build_desired_tasks, build_task_action, resolve_worker_invocation


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
    assert invocation.arguments == "-m selfsnap capture --trigger scheduled --schedule-id morning"
    assert invocation.working_directory == str(temp_paths.root)


def test_build_desired_tasks_still_returns_tasks_while_sync_state_is_failed(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.mark_scheduler_sync_failed("previous sync failure")
    config.schedules = [Schedule(schedule_id="morning", label="Morning", local_time="09:00", enabled=True)]

    desired = build_desired_tasks(temp_paths, config)

    assert set(desired) == {"SelfSnap.Capture.morning"}


def test_resolve_worker_invocation_uses_cmd_for_wrapper(temp_paths) -> None:
    temp_paths.ensure_dirs()
    wrapper = temp_paths.bin_dir / "SelfSnap.cmd"
    wrapper.write_text("@echo off\r\n", encoding="ascii")

    invocation = resolve_worker_invocation(temp_paths, "morning")

    assert invocation.executable.lower().endswith("cmd.exe")
    assert "SelfSnap.cmd" in invocation.arguments
    assert "--schedule-id morning" in invocation.arguments
