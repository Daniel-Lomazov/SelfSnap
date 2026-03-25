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
    purged_utc,
    app_version,
    created_utc
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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


def get_recent(connection: sqlite3.Connection, n: int = 10) -> list[CaptureRecord]:
    rows = connection.execute(
        """
        SELECT *
        FROM capture_records
        WHERE image_path IS NOT NULL AND file_present = 1
        ORDER BY started_utc DESC
        LIMIT ?
        """,
        (n,),
    ).fetchall()
    return [CaptureRecord.from_row(dict(row)) for row in rows]


def summary_stats(connection: sqlite3.Connection) -> dict[str, object]:
    """Return aggregate statistics about all capture records."""
    row = connection.execute(
        """
        SELECT
            COUNT(*) AS total_captures,
            SUM(CASE WHEN outcome_category = 'success' THEN 1 ELSE 0 END) AS total_success,
            SUM(CASE WHEN outcome_category = 'missed' THEN 1 ELSE 0 END) AS total_missed,
            SUM(CASE WHEN outcome_category = 'failed' THEN 1 ELSE 0 END) AS total_failed,
            SUM(CASE WHEN outcome_category = 'skipped' THEN 1 ELSE 0 END) AS total_skipped,
            COALESCE(SUM(file_bytes), 0) AS total_bytes,
            COUNT(DISTINCT schedule_id) AS distinct_schedules
        FROM capture_records
        """
    ).fetchone()
    if row is None:
        return {}
    return dict(row)


def daily_counts(connection: sqlite3.Connection, days: int = 30) -> list[tuple[str, int]]:
    """Return (date_str, count) tuples for the last N days, ordered ascending."""
    rows = connection.execute(
        """
        SELECT DATE(COALESCE(started_utc, created_utc)) AS day, COUNT(*) AS cnt
        FROM capture_records
        WHERE DATE(COALESCE(started_utc, created_utc)) >= DATE('now', ? || ' days')
        GROUP BY day
        ORDER BY day ASC
        """,
        (f"-{days}",),
    ).fetchall()
    return [(row["day"], row["cnt"]) for row in rows]


def get_by_schedule(
    connection: sqlite3.Connection, schedule_id: str, limit: int = 5
) -> list[CaptureRecord]:
    """Return the most recent capture records for a specific schedule."""
    rows = connection.execute(
        """
        SELECT *
        FROM capture_records
        WHERE schedule_id = ?
        ORDER BY COALESCE(started_utc, created_utc) DESC
        LIMIT ?
        """,
        (schedule_id, limit),
    ).fetchall()
    return [CaptureRecord.from_row(dict(row)) for row in rows]


def mark_record_purged(
    connection: sqlite3.Connection, record_id: str, purged_utc: str
) -> None:
    """Mark a record as permanently purged (file deleted from archive)."""
    connection.execute(
        """
        UPDATE capture_records
        SET purged_utc = ?,
            file_present = 0
        WHERE record_id = ?
        """,
        (purged_utc, record_id),
    )
    connection.commit()


def get_purge_candidates(
    connection: sqlite3.Connection, grace_cutoff_utc: str
) -> list[CaptureRecord]:
    """Return archived records whose archive time is older than the grace cutoff."""
    rows = connection.execute(
        """
        SELECT *
        FROM capture_records
        WHERE archived = 1
          AND purged_utc IS NULL
          AND archived_at_utc IS NOT NULL
          AND archived_at_utc < ?
        ORDER BY archived_at_utc ASC
        """,
        (grace_cutoff_utc,),
    ).fetchall()
    return [CaptureRecord.from_row(dict(row)) for row in rows]
