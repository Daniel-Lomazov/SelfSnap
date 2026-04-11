from __future__ import annotations

from pathlib import Path
import sqlite3
from types import TracebackType
from typing import Literal


class ManagedConnection(sqlite3.Connection):
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()
        return False


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
    archived INTEGER NOT NULL DEFAULT 0,
    archived_at_utc TEXT NULL,
    retention_deleted_at_utc TEXT NULL,
    purged_utc TEXT NULL,
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
    connection = sqlite3.connect(
        db_path,
        timeout=30,
        factory=ManagedConnection,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


def ensure_database(db_path: Path) -> None:
    with connect(db_path) as connection:
        connection.execute(CREATE_CAPTURE_RECORDS)
        _ensure_column(connection, "capture_records", "archived", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(connection, "capture_records", "archived_at_utc", "TEXT NULL")
        _ensure_column(connection, "capture_records", "retention_deleted_at_utc", "TEXT NULL")
        _ensure_column(connection, "capture_records", "purged_utc", "TEXT NULL")
        for statement in CREATE_INDEXES:
            connection.execute(statement)
        connection.commit()


def _ensure_column(
    connection: sqlite3.Connection, table_name: str, column_name: str, column_definition: str
) -> None:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    if any(row["name"] == column_name for row in rows):
        return
    connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
