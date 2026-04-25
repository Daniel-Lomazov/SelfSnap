from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.db import connect, ensure_database
from selfsnap.models import CaptureBackendError, Schedule, TriggerSource
from selfsnap.records import get_latest_record
from selfsnap.worker import (
    EXIT_CONFIG_FAILURE,
    EXIT_OK,
    EXIT_OPERATIONAL_FAILURE,
    EXIT_SCHEDULER_FAILURE,
    run_capture_command,
)


@dataclass
class FakeImage:
    payload: bytes = b"fake-png"

    def save(self, destination, format: str = "PNG", **kwargs) -> None:  # noqa: A002
        Path(destination).write_bytes(self.payload)


@dataclass
class FakeCapture:
    images: list[FakeImage]
    monitor_count: int = 2
    composite_width: int = 3200
    composite_height: int = 1080


def test_manual_capture_writes_file_and_db_row(temp_paths, monkeypatch) -> None:
    config = load_or_create_config(temp_paths)
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
    ensure_database(temp_paths.db_path)

    monkeypatch.setattr("selfsnap.worker.capture_composite", lambda: FakeCapture([FakeImage()]))

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

    monkeypatch.setattr("selfsnap.worker.capture_composite", lambda: FakeCapture([FakeImage()]))

    result = run_capture_command(TriggerSource.MANUAL, paths=temp_paths)

    assert result.exit_code == EXIT_OK
    assert result.record is not None
    assert result.record.outcome_code == "capture_saved"


def test_scheduled_capture_is_blocked_when_scheduler_sync_failed(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.mark_scheduler_sync_failed("task creation failed")
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


def test_high_frequency_scheduled_capture_is_not_blocked_by_scheduler_sync_failed(
    temp_paths, monkeypatch
) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.mark_scheduler_sync_failed("task creation failed")
    config.schedules = [
        Schedule(
            schedule_id="break",
            label="Break",
            interval_value=5,
            interval_unit="minute",
            start_date_local="2026-03-23",
            start_time_local="14:00:00",
        )
    ]
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)
    monkeypatch.setattr("selfsnap.worker.capture_composite", lambda: FakeCapture([FakeImage()]))

    result = run_capture_command(
        TriggerSource.SCHEDULED,
        schedule_id="break",
        planned_local_ts="2026-03-23T14:05:00+02:00",
        paths=temp_paths,
    )

    assert result.exit_code == EXIT_OK
    assert result.record is not None
    assert result.record.outcome_code == "capture_saved"


def test_per_monitor_capture_writes_multiple_monitor_files(temp_paths, monkeypatch) -> None:
    config = load_or_create_config(temp_paths)
    config.capture_mode = "per_monitor"
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)

    monkeypatch.setattr(
        "selfsnap.worker.capture_per_monitor",
        lambda: FakeCapture([FakeImage(b"m1"), FakeImage(b"m2")], monitor_count=2),
    )

    result = run_capture_command(TriggerSource.MANUAL, paths=temp_paths)

    assert result.exit_code == EXIT_OK
    assert result.record is not None
    assert result.record.image_path is not None
    first_path = Path(result.record.image_path)
    second_path = first_path.with_name(first_path.stem.replace("_m1", "_m2") + first_path.suffix)
    assert first_path.exists()
    assert second_path.exists()
    assert first_path.suffix == ".png"
    assert second_path.suffix == ".png"
    # The zero-byte reservation placeholder (no _m1/_m2 suffix) must be removed.
    ghost = first_path.with_name(first_path.name.replace("_m1", ""))
    assert not ghost.exists(), f"Ghost reservation file was not cleaned up: {ghost}"


def test_composite_capture_honors_image_format_and_quality(temp_paths, monkeypatch) -> None:
    config = load_or_create_config(temp_paths)
    config.capture_mode = "composite"
    config.image_format = "jpeg"
    config.image_quality = 77
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)

    saved_calls: list[tuple[str, int | None]] = []

    class RecordingImage(FakeImage):
        def save(self, destination, format: str = "PNG", **kwargs) -> None:  # noqa: A002
            saved_calls.append((format, kwargs.get("quality")))
            Path(destination).write_bytes(self.payload)

    monkeypatch.setattr(
        "selfsnap.worker.capture_composite",
        lambda: FakeCapture([RecordingImage(b"jpeg-bytes")], monitor_count=1),
    )

    result = run_capture_command(TriggerSource.MANUAL, paths=temp_paths)

    assert result.exit_code == EXIT_OK
    assert result.record is not None
    assert result.record.image_path is not None
    assert Path(result.record.image_path).suffix == ".jpeg"
    assert saved_calls == [("JPEG", 77)]


# ---------------------------------------------------------------------------
# Scheduled capture — skip conditions
# ---------------------------------------------------------------------------


def _scheduled_config(temp_paths, *, first_run: bool = True, app_enabled: bool = True):
    config = load_or_create_config(temp_paths)
    config.first_run_completed = first_run
    config.app_enabled = app_enabled
    config.schedules = [
        Schedule(
            schedule_id="morning",
            label="Morning",
            interval_value=1,
            interval_unit="day",
            start_date_local="2026-01-01",
            start_time_local="09:00:00",
        )
    ]
    save_config(temp_paths, config)
    return config


def test_scheduled_capture_skipped_when_first_run_incomplete(temp_paths, monkeypatch) -> None:
    _scheduled_config(temp_paths, first_run=False, app_enabled=True)
    ensure_database(temp_paths.db_path)
    monkeypatch.setattr(
        "selfsnap.worker.capture_composite",
        lambda: (_ for _ in ()).throw(RuntimeError("should not be called")),
    )

    result = run_capture_command(
        TriggerSource.SCHEDULED,
        schedule_id="morning",
        planned_local_ts="2026-04-03T09:00:00+02:00",
        paths=temp_paths,
    )

    assert result.exit_code == EXIT_OK
    assert result.record is not None
    assert result.record.outcome_code == "scheduled_disabled"
    assert result.record.outcome_category == "skipped"
    assert "first-run" in (result.record.error_message or "")


def test_scheduled_capture_skipped_when_app_disabled(temp_paths, monkeypatch) -> None:
    _scheduled_config(temp_paths, first_run=True, app_enabled=False)
    ensure_database(temp_paths.db_path)

    result = run_capture_command(
        TriggerSource.SCHEDULED,
        schedule_id="morning",
        planned_local_ts="2026-04-03T09:00:00+02:00",
        paths=temp_paths,
    )

    assert result.exit_code == EXIT_OK
    assert result.record is not None
    assert result.record.outcome_code == "scheduled_disabled"
    assert "app_enabled" in (result.record.error_message or "")


def test_scheduled_capture_skipped_when_schedule_is_disabled(temp_paths, monkeypatch) -> None:
    config = _scheduled_config(temp_paths, first_run=True, app_enabled=True)
    config.schedules[0].enabled = False
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)

    result = run_capture_command(
        TriggerSource.SCHEDULED,
        schedule_id="morning",
        planned_local_ts="2026-04-03T09:00:00+02:00",
        paths=temp_paths,
    )

    assert result.exit_code == EXIT_OK
    assert result.record is not None
    assert result.record.outcome_code == "scheduled_disabled"
    assert "schedule is disabled" in (result.record.error_message or "")


def test_scheduled_capture_fails_for_unknown_schedule_id(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)

    result = run_capture_command(
        TriggerSource.SCHEDULED,
        schedule_id="no_such_schedule",
        planned_local_ts="2026-04-03T09:00:00+02:00",
        paths=temp_paths,
    )

    assert result.exit_code == EXIT_CONFIG_FAILURE
    assert result.record is None


# ---------------------------------------------------------------------------
# Capture backend error path
# ---------------------------------------------------------------------------


def test_capture_backend_error_records_failure(temp_paths, monkeypatch) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)

    monkeypatch.setattr(
        "selfsnap.worker.capture_composite",
        lambda: (_ for _ in ()).throw(CaptureBackendError("mss not available")),
    )

    result = run_capture_command(TriggerSource.MANUAL, paths=temp_paths)

    assert result.exit_code == EXIT_OPERATIONAL_FAILURE
    assert result.record is not None
    assert result.record.outcome_code == "capture_backend_error"
    assert result.record.outcome_category == "failed"
    assert "mss not available" in result.message


# ---------------------------------------------------------------------------
# Config validation failure path
# ---------------------------------------------------------------------------


def test_config_validation_failure_returns_config_exit_code(temp_paths, monkeypatch) -> None:
    monkeypatch.setattr(
        "selfsnap.worker.load_or_create_config",
        lambda _: (_ for _ in ()).throw(
            __import__("selfsnap.models", fromlist=["ConfigValidationError"]).ConfigValidationError(
                "bad config"
            )
        ),
    )
    ensure_database(temp_paths.db_path)

    result = run_capture_command(TriggerSource.MANUAL, paths=temp_paths)

    assert result.exit_code == EXIT_CONFIG_FAILURE
    assert result.record is None
