from __future__ import annotations

from selfsnap.scheduler.task_scheduler import build_task_action


def test_build_task_action_includes_schedule_id(temp_paths) -> None:
    action = build_task_action(temp_paths, "afternoon")
    assert "capture --trigger scheduled --schedule-id afternoon" in action
