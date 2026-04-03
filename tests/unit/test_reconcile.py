from __future__ import annotations

from datetime import datetime, timezone

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.db import connect, ensure_database
from selfsnap.models import Schedule
from selfsnap.records import list_recent_records
from selfsnap.scheduler.reconcile import reconcile_missed_slots


def test_reconcile_does_not_print_when_emit_console_is_false(temp_paths, capsys) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    save_config(temp_paths, config)

    result = reconcile_missed_slots(temp_paths, emit_console=False)

    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == ""


def test_reconcile_records_missed_coarse_occurrences(temp_paths, monkeypatch) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.schedules = [
        Schedule(
            schedule_id="hourly",
            label="Hourly",
            interval_value=1,
            interval_unit="hour",
            start_date_local="2026-03-23",
            start_time_local="08:00:00",
        )
    ]
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)

    fake_now = datetime(2026, 3, 23, 10, 10, 0, tzinfo=timezone.utc)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fake_now.replace(tzinfo=None)
            return fake_now.astimezone(tz)

    monkeypatch.setattr("selfsnap.scheduler.reconcile.datetime", FrozenDatetime)

    result = reconcile_missed_slots(temp_paths, emit_console=False)

    assert result == 0
    with connect(temp_paths.db_path) as connection:
        records = list_recent_records(connection, limit=5)
    planned = {record.planned_local_ts for record in records}
    local_tz = fake_now.replace(tzinfo=None).astimezone().tzinfo
    assert datetime(2026, 3, 23, 8, 0, 0, tzinfo=local_tz).isoformat() in planned
    assert datetime(2026, 3, 23, 9, 0, 0, tzinfo=local_tz).isoformat() in planned


# ---------------------------------------------------------------------------
# Early-exit branches
# ---------------------------------------------------------------------------


def test_reconcile_skips_when_first_run_not_completed(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = False
    config.app_enabled = True
    save_config(temp_paths, config)

    result = reconcile_missed_slots(temp_paths)

    assert result == 0


def test_reconcile_skips_when_app_disabled(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = False
    save_config(temp_paths, config)

    result = reconcile_missed_slots(temp_paths)

    assert result == 0


def test_reconcile_skips_when_scheduler_sync_failed(temp_paths) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.scheduler_sync_state = "failed"
    save_config(temp_paths, config)

    result = reconcile_missed_slots(temp_paths)

    assert result == 0


def test_reconcile_emits_console_output_when_flag_set(temp_paths, capsys) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    save_config(temp_paths, config)

    result = reconcile_missed_slots(temp_paths, emit_console=True)

    captured = capsys.readouterr()
    assert result == 0
    assert "Reconcile completed" in captured.out


def test_reconcile_skips_non_coarse_schedules(temp_paths, monkeypatch) -> None:
    """Fine schedules (seconds/minutes) should not be tracked by reconcile."""
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.schedules = [
        Schedule(
            schedule_id="every_30s",
            label="Every 30 seconds",
            interval_value=30,
            interval_unit="second",
            start_date_local="2026-03-23",
            start_time_local="08:00:00",
        )
    ]
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)

    fake_now = datetime(2026, 3, 23, 10, 10, 0, tzinfo=timezone.utc)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fake_now.replace(tzinfo=None)
            return fake_now.astimezone(tz)

    monkeypatch.setattr("selfsnap.scheduler.reconcile.datetime", FrozenDatetime)

    result = reconcile_missed_slots(temp_paths)

    assert result == 0
    with connect(temp_paths.db_path) as connection:
        records = list_recent_records(connection, limit=5)
    assert records == []


def test_reconcile_skips_already_existing_slot(temp_paths, monkeypatch) -> None:
    """Line 50: has_record_for_slot → continue skips duplicates."""
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    config.schedules = [
        Schedule(
            schedule_id="hourly2",
            label="Hourly 2",
            interval_value=1,
            interval_unit="hour",
            start_date_local="2026-03-23",
            start_time_local="08:00:00",
        )
    ]
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)

    fake_now = datetime(2026, 3, 23, 10, 10, 0, tzinfo=timezone.utc)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fake_now.replace(tzinfo=None)
            return fake_now.astimezone(tz)

    monkeypatch.setattr("selfsnap.scheduler.reconcile.datetime", FrozenDatetime)

    # First reconcile creates missed records
    reconcile_missed_slots(temp_paths, emit_console=False)
    with connect(temp_paths.db_path) as connection:
        count_after_first = len(list_recent_records(connection, limit=100))

    # Second reconcile should find all existing records and skip them (line 50: continue)
    reconcile_missed_slots(temp_paths, emit_console=False)
    with connect(temp_paths.db_path) as connection:
        count_after_second = len(list_recent_records(connection, limit=100))

    # No new records should have been created on the second run
    assert count_after_first >= 1
    assert count_after_first == count_after_second
