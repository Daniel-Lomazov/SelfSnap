from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from selfsnap.config_store import load_or_create_config
from selfsnap.db import connect, ensure_database
from selfsnap.logging_setup import setup_logging
from selfsnap.models import CaptureRecord, OutcomeCategory, OutcomeCode, TriggerSource
from selfsnap.paths import AppPaths, resolve_app_paths
from selfsnap.records import has_record_for_slot, insert_capture_record
from selfsnap.recurrence import is_coarse_schedule, iter_occurrences_between
from selfsnap.version import __version__
from selfsnap.worker import EXIT_OK

RECONCILE_LOOKBACK_HOURS = 12


def reconcile_missed_slots(paths: AppPaths | None = None, emit_console: bool = False) -> int:
    paths = paths or resolve_app_paths()
    config = load_or_create_config(paths)
    logger = setup_logging(paths, config.log_level)
    ensure_database(paths.db_path)

    if not config.first_run_completed:
        logger.info("Reconcile skipped because first-run setup is incomplete")
        return EXIT_OK

    if not config.app_enabled:
        logger.info("Reconcile skipped because app_enabled is false")
        return EXIT_OK

    if config.scheduler_sync_failed():
        logger.info("Reconcile skipped because scheduler sync is in failed state")
        return EXIT_OK

    now_local = datetime.now().astimezone()
    start_local = now_local - timedelta(hours=RECONCILE_LOOKBACK_HOURS)
    cutoff_local = now_local - timedelta(seconds=config.slot_match_tolerance_seconds)
    created = 0

    with connect(paths.db_path) as connection:
        for schedule in config.schedules:
            if not schedule.enabled or not is_coarse_schedule(schedule):
                continue
            for planned in iter_occurrences_between(schedule, start_local, cutoff_local):
                planned_local_ts = planned.isoformat()
                if has_record_for_slot(connection, schedule.schedule_id, planned_local_ts):
                    continue
                record = CaptureRecord(
                    record_id=str(uuid4()),
                    trigger_source=TriggerSource.RECONCILE.value,
                    schedule_id=schedule.schedule_id,
                    planned_local_ts=planned_local_ts,
                    started_utc=None,
                    finished_utc=None,
                    outcome_category=OutcomeCategory.MISSED.value,
                    outcome_code=OutcomeCode.SLOT_MISSED_NO_ATTEMPT.value,
                    image_path=None,
                    file_present=False,
                    image_sha256=None,
                    monitor_count=None,
                    composite_width=None,
                    composite_height=None,
                    file_bytes=None,
                    error_code=OutcomeCode.SLOT_MISSED_NO_ATTEMPT.value,
                    error_message="No capture attempt was recorded for the planned schedule slot.",
                    archived=False,
                    archived_at_utc=None,
                    retention_deleted_at_utc=None,
                    app_version=__version__,
                    created_utc=datetime.now(UTC).isoformat(),
                )
                insert_capture_record(connection, record)
                created += 1

    logger.info("Reconcile completed, created %s missed-slot records", created)
    if emit_console:
        print(f"Reconcile completed, created {created} missed-slot records")
    return EXIT_OK
