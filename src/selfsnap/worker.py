from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import logging
from pathlib import Path
import traceback
from uuid import uuid4

from selfsnap.capture_engine import capture_virtual_desktop
from selfsnap.config_store import load_or_create_config
from selfsnap.db import connect, ensure_database
from selfsnap.models import (
    AppConfig,
    CaptureBackendError,
    CaptureRecord,
    ConfigValidationError,
    OutcomeCategory,
    OutcomeCode,
    TriggerSource,
)
from selfsnap.paths import AppPaths, resolve_app_paths
from selfsnap.records import insert_capture_record
from selfsnap.retention import apply_retention
from selfsnap.version import __version__


EXIT_OK = 0
EXIT_OPERATIONAL_FAILURE = 1
EXIT_CONFIG_FAILURE = 2
EXIT_SCHEDULER_FAILURE = 3
EXIT_UNEXPECTED = 9


@dataclass(slots=True)
class WorkerCommandResult:
    exit_code: int
    record: CaptureRecord | None
    message: str


def run_capture_command(
    trigger_source: TriggerSource,
    schedule_id: str | None = None,
    planned_local_ts: str | None = None,
    paths: AppPaths | None = None,
) -> WorkerCommandResult:
    paths = paths or resolve_app_paths()
    paths.ensure_dirs()

    logger = logging.getLogger("selfsnap")
    config: AppConfig | None = None

    try:
        config = load_or_create_config(paths)
        ensure_database(paths.db_path)
    except ConfigValidationError as exc:
        logger.exception("Configuration validation failed")
        return WorkerCommandResult(EXIT_CONFIG_FAILURE, None, str(exc))
    except Exception as exc:
        logger.exception("Unexpected initialization failure")
        return WorkerCommandResult(EXIT_UNEXPECTED, None, str(exc))

    with connect(paths.db_path) as connection:
        now_local = datetime.now().astimezone()
        if trigger_source == TriggerSource.SCHEDULED and schedule_id is not None:
            schedule = config.get_schedule(schedule_id)
            if schedule is None:
                return WorkerCommandResult(EXIT_CONFIG_FAILURE, None, f"Unknown schedule_id: {schedule_id}")
            if planned_local_ts is None:
                planned_local_ts = datetime.combine(
                    now_local.date(),
                    datetime.strptime(schedule.local_time, "%H:%M").time(),
                    tzinfo=now_local.tzinfo,
                ).isoformat()

            if not config.app_enabled:
                record = _build_non_capture_record(
                    trigger_source=trigger_source,
                    schedule_id=schedule_id,
                    planned_local_ts=planned_local_ts,
                    category=OutcomeCategory.SKIPPED,
                    code=OutcomeCode.SCHEDULED_DISABLED,
                    error_message="Scheduled capture skipped because app_enabled is false.",
                )
                insert_capture_record(connection, record)
                return WorkerCommandResult(EXIT_OK, record, record.error_message or "")

            if not schedule.enabled:
                record = _build_non_capture_record(
                    trigger_source=trigger_source,
                    schedule_id=schedule_id,
                    planned_local_ts=planned_local_ts,
                    category=OutcomeCategory.SKIPPED,
                    code=OutcomeCode.SCHEDULED_DISABLED,
                    error_message="Scheduled capture skipped because the schedule is disabled.",
                )
                insert_capture_record(connection, record)
                return WorkerCommandResult(EXIT_OK, record, record.error_message or "")

            if config.is_paused(now_local):
                record = _build_non_capture_record(
                    trigger_source=trigger_source,
                    schedule_id=schedule_id,
                    planned_local_ts=planned_local_ts,
                    category=OutcomeCategory.SKIPPED,
                    code=OutcomeCode.SCHEDULED_PAUSED,
                    error_message="Scheduled capture skipped because the app is paused.",
                )
                insert_capture_record(connection, record)
                return WorkerCommandResult(EXIT_OK, record, record.error_message or "")

        started_utc = datetime.now(timezone.utc)
        try:
            capture = capture_virtual_desktop()
            capture_root = paths.resolve_capture_root(config)
            destination = paths.capture_file_path(capture_root, now_local, trigger_source, schedule_id)
            destination.parent.mkdir(parents=True, exist_ok=True)
            capture.image.save(destination, format="PNG")
            file_bytes = destination.stat().st_size
            image_hash = _hash_file(destination)
            finished_utc = datetime.now(timezone.utc)
            record = CaptureRecord(
                record_id=str(uuid4()),
                trigger_source=trigger_source.value,
                schedule_id=schedule_id,
                planned_local_ts=planned_local_ts,
                started_utc=started_utc.isoformat(),
                finished_utc=finished_utc.isoformat(),
                outcome_category=OutcomeCategory.SUCCESS.value,
                outcome_code=OutcomeCode.CAPTURE_SAVED.value,
                image_path=str(destination),
                file_present=True,
                image_sha256=image_hash,
                monitor_count=capture.monitor_count,
                composite_width=capture.composite_width,
                composite_height=capture.composite_height,
                file_bytes=file_bytes,
                error_code=None,
                error_message=None,
                retention_deleted_at_utc=None,
                app_version=__version__,
                created_utc=finished_utc.isoformat(),
            )
            insert_capture_record(connection, record)
            apply_retention(connection, config)
            return WorkerCommandResult(EXIT_OK, record, f"Capture saved to {destination}")
        except CaptureBackendError as exc:
            record = _build_failure_record(
                trigger_source=trigger_source,
                schedule_id=schedule_id,
                planned_local_ts=planned_local_ts,
                started_utc=started_utc,
                code=OutcomeCode.CAPTURE_BACKEND_ERROR,
                message=str(exc),
            )
            insert_capture_record(connection, record)
            return WorkerCommandResult(EXIT_OPERATIONAL_FAILURE, record, str(exc))
        except OSError as exc:
            record = _build_failure_record(
                trigger_source=trigger_source,
                schedule_id=schedule_id,
                planned_local_ts=planned_local_ts,
                started_utc=started_utc,
                code=OutcomeCode.IMAGE_WRITE_ERROR,
                message=str(exc),
            )
            insert_capture_record(connection, record)
            return WorkerCommandResult(EXIT_OPERATIONAL_FAILURE, record, str(exc))
        except Exception as exc:  # pragma: no cover - final safety net
            logger.error("Unexpected worker failure\n%s", traceback.format_exc())
            record = _build_failure_record(
                trigger_source=trigger_source,
                schedule_id=schedule_id,
                planned_local_ts=planned_local_ts,
                started_utc=started_utc,
                code=OutcomeCode.UNEXPECTED_ERROR,
                message=str(exc),
            )
            try:
                insert_capture_record(connection, record)
            except Exception:
                logger.exception("Failed to persist unexpected failure record")
            return WorkerCommandResult(EXIT_UNEXPECTED, record, str(exc))


def _build_non_capture_record(
    trigger_source: TriggerSource,
    schedule_id: str | None,
    planned_local_ts: str | None,
    category: OutcomeCategory,
    code: OutcomeCode,
    error_message: str,
) -> CaptureRecord:
    now_utc = datetime.now(timezone.utc)
    return CaptureRecord(
        record_id=str(uuid4()),
        trigger_source=trigger_source.value,
        schedule_id=schedule_id,
        planned_local_ts=planned_local_ts,
        started_utc=None,
        finished_utc=None,
        outcome_category=category.value,
        outcome_code=code.value,
        image_path=None,
        file_present=False,
        image_sha256=None,
        monitor_count=None,
        composite_width=None,
        composite_height=None,
        file_bytes=None,
        error_code=code.value,
        error_message=error_message,
        retention_deleted_at_utc=None,
        app_version=__version__,
        created_utc=now_utc.isoformat(),
    )


def _build_failure_record(
    trigger_source: TriggerSource,
    schedule_id: str | None,
    planned_local_ts: str | None,
    started_utc: datetime,
    code: OutcomeCode,
    message: str,
) -> CaptureRecord:
    finished_utc = datetime.now(timezone.utc)
    return CaptureRecord(
        record_id=str(uuid4()),
        trigger_source=trigger_source.value,
        schedule_id=schedule_id,
        planned_local_ts=planned_local_ts,
        started_utc=started_utc.isoformat(),
        finished_utc=finished_utc.isoformat(),
        outcome_category=OutcomeCategory.FAILED.value,
        outcome_code=code.value,
        image_path=None,
        file_present=False,
        image_sha256=None,
        monitor_count=None,
        composite_width=None,
        composite_height=None,
        file_bytes=None,
        error_code=code.value,
        error_message=message,
        retention_deleted_at_utc=None,
        app_version=__version__,
        created_utc=finished_utc.isoformat(),
    )


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()

