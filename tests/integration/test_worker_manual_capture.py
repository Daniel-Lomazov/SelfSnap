from __future__ import annotations

from dataclasses import dataclass

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.db import connect, ensure_database
from selfsnap.models import Schedule, TriggerSource
from selfsnap.records import get_latest_record
from selfsnap.worker import EXIT_OK, EXIT_SCHEDULER_FAILURE, run_capture_command


@dataclass
class FakeImage:
    payload: bytes = b"fake-png"

    def save(self, destination, format: str = "PNG") -> None:  # noqa: A002
        destination.write_bytes(self.payload)


@dataclass
class FakeCapture:
    image: FakeImage
    monitor_count: int = 2
    composite_width: int = 3200
    composite_height: int = 1080


def test_manual_capture_writes_file_and_db_row(temp_paths, monkeypatch) -> None:
    config = load_or_create_config(temp_paths)
    config.schedules = [Schedule(schedule_id="afternoon", label="Afternoon", local_time="14:00")]
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)

    monkeypatch.setattr("selfsnap.worker.capture_virtual_desktop", lambda: FakeCapture(FakeImage()))

    result = run_capture_command(TriggerSource.MANUAL, paths=temp_paths)

    assert result.exit_code == EXIT_OK
    assert result.record is not None
    assert result.record.image_path is not None

    with connect(temp_paths.db_path) as connection:
        latest = get_latest_record(connection)

    assert latest is not None
    assert latest.outcome_code == "capture_saved"
    assert latest.archived is False
    assert latest.archived_at_utc is None


def test_manual_capture_is_allowed_when_scheduler_sync_failed(temp_paths, monkeypatch) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.mark_scheduler_sync_failed("task creation failed")
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)

    monkeypatch.setattr("selfsnap.worker.capture_virtual_desktop", lambda: FakeCapture(FakeImage()))

    result = run_capture_command(TriggerSource.MANUAL, paths=temp_paths)

    assert result.exit_code == EXIT_OK
    assert result.record is not None
    assert result.record.outcome_code == "capture_saved"


def test_scheduled_capture_is_blocked_when_scheduler_sync_failed(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.mark_scheduler_sync_failed("task creation failed")
    config.schedules = [Schedule(schedule_id="afternoon", label="Afternoon", local_time="14:00")]
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)

    result = run_capture_command(
        TriggerSource.SCHEDULED,
        schedule_id="afternoon",
        planned_local_ts="2026-03-22T14:00:00+02:00",
        paths=temp_paths,
    )

    assert result.exit_code == EXIT_SCHEDULER_FAILURE
    assert result.record is not None
    assert result.record.outcome_code == "scheduler_sync_error"
