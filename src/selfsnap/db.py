from __future__ import annotations

from pathlib import Path
import sqlite3


CREATE_CAPTURE_RECORDS = """
CREATE TABLE IF NOT EXISTS capture_records (
    record_id TEXT PRIMARY KEY,
    trigger_source TEXT NOT NULL,
    schedule_id TEXT NULL,
    planned_local_ts TEXT NULL,
    started_utc TEXT NULL,
    finished_utc TEXT NULL,
    outcome_category TEXT NOT NULL,
    outcome_code TEXT NOT NULL,
    image_path TEXT NULL,
    file_present INTEGER NOT NULL,
    image_sha256 TEXT NULL,
    monitor_count INTEGER NULL,
    composite_width INTEGER NULL,
    composite_height INTEGER NULL,
    file_bytes INTEGER NULL,
    error_code TEXT NULL,
    error_message TEXT NULL,
    retention_deleted_at_utc TEXT NULL,
    app_version TEXT NOT NULL,
    created_utc TEXT NOT NULL
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_capture_records_planned_local_ts ON capture_records(planned_local_ts);",
    "CREATE INDEX IF NOT EXISTS idx_capture_records_started_utc ON capture_records(started_utc);",
    "CREATE INDEX IF NOT EXISTS idx_capture_records_outcome_category ON capture_records(outcome_category);",
    "CREATE INDEX IF NOT EXISTS idx_capture_records_schedule_id ON capture_records(schedule_id);",
]


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_database(db_path: Path) -> None:
    with connect(db_path) as connection:
        connection.execute(CREATE_CAPTURE_RECORDS)
        for statement in CREATE_INDEXES:
            connection.execute(statement)
        connection.commit()

