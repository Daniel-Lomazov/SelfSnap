from __future__ import annotations

from pathlib import Path
import sqlite3

from selfsnap.models import CaptureRecord


INSERT_CAPTURE_RECORD = """
INSERT INTO capture_records (
    record_id,
    trigger_source,
    schedule_id,
    planned_local_ts,
    started_utc,
    finished_utc,
    outcome_category,
    outcome_code,
    image_path,
    file_present,
    image_sha256,
    monitor_count,
    composite_width,
    composite_height,
    file_bytes,
    error_code,
    error_message,
    archived,
    archived_at_utc,
    retention_deleted_at_utc,
    app_version,
    created_utc
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


def insert_capture_record(connection: sqlite3.Connection, record: CaptureRecord) -> None:
    connection.execute(INSERT_CAPTURE_RECORD, record.to_db_tuple())
    connection.commit()


def get_latest_record(connection: sqlite3.Connection) -> CaptureRecord | None:
    row = connection.execute(
        "SELECT * FROM capture_records ORDER BY created_utc DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    return CaptureRecord.from_row(dict(row))


def has_record_for_slot(
    connection: sqlite3.Connection,
    schedule_id: str,
    planned_local_ts: str,
) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM capture_records
        WHERE schedule_id = ?
          AND planned_local_ts IS NOT NULL
          AND planned_local_ts = ?
        LIMIT 1
        """,
        (schedule_id, planned_local_ts),
    ).fetchone()
    return row is not None


def get_retention_candidates(connection: sqlite3.Connection, cutoff_utc: str) -> list[CaptureRecord]:
    rows = connection.execute(
        """
        SELECT *
        FROM capture_records
        WHERE image_path IS NOT NULL
          AND file_present = 1
          AND archived = 0
          AND retention_deleted_at_utc IS NULL
          AND COALESCE(finished_utc, created_utc) < ?
        ORDER BY COALESCE(finished_utc, created_utc) ASC
        """,
        (cutoff_utc,),
    ).fetchall()
    return [CaptureRecord.from_row(dict(row)) for row in rows]


def mark_record_archived(
    connection: sqlite3.Connection, record_id: str, archived_path: str, archived_at_utc: str
) -> None:
    connection.execute(
        """
        UPDATE capture_records
        SET image_path = ?,
            archived = 1,
            archived_at_utc = ?,
            file_present = 1
        WHERE record_id = ?
        """,
        (archived_path, archived_at_utc, record_id),
    )
    connection.commit()


def resolve_latest_capture_path(connection: sqlite3.Connection) -> Path | None:
    row = connection.execute(
        """
        SELECT image_path
        FROM capture_records
        WHERE image_path IS NOT NULL AND file_present = 1
        ORDER BY created_utc DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None or row["image_path"] is None:
        return None
    return Path(row["image_path"])


def list_recent_records(connection: sqlite3.Connection, limit: int = 20) -> list[CaptureRecord]:
    rows = connection.execute(
        "SELECT * FROM capture_records ORDER BY created_utc DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [CaptureRecord.from_row(dict(row)) for row in rows]


def list_all_record_paths(connection: sqlite3.Connection) -> list[Path]:
    rows = connection.execute(
        """
        SELECT DISTINCT image_path
        FROM capture_records
        WHERE image_path IS NOT NULL
        """
    ).fetchall()
    return [Path(row["image_path"]) for row in rows if row["image_path"]]


def clear_capture_history(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM capture_records")
    connection.commit()
