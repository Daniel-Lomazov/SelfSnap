"""Tests for selfsnap.db — connection management and schema utilities."""

from __future__ import annotations

import sqlite3

import pytest

from selfsnap.db import ManagedConnection, _ensure_column, connect, ensure_database

# ---------------------------------------------------------------------------
# ManagedConnection — commit / rollback behaviour
# ---------------------------------------------------------------------------


def test_managed_connection_commits_on_clean_exit(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        conn.execute(
            "INSERT INTO capture_records("
            " record_id, trigger_source, outcome_category, outcome_code,"
            " file_present, archived, app_version, created_utc"
            ") VALUES ("
            "'test-1', 'manual', 'success', 'capture_saved', 0, 0,"
            " '1.0', '2026-01-01T00:00:00'"
            ")"
        )
    # Re-open to verify the row was committed
    with connect(temp_paths.db_path) as conn:
        row = conn.execute(
            "SELECT record_id FROM capture_records WHERE record_id='test-1'"
        ).fetchone()
    assert row is not None
    assert row["record_id"] == "test-1"


def test_managed_connection_rolls_back_on_exception(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    try:
        with connect(temp_paths.db_path) as conn:
            conn.execute(
                "INSERT INTO capture_records("
                " record_id, trigger_source, outcome_category, outcome_code,"
                " file_present, archived, app_version, created_utc"
                ") VALUES ("
                "'rollback-1', 'manual', 'success', 'capture_saved', 0, 0,"
                " '1.0', '2026-01-01T00:00:00'"
                ")"
            )
            raise RuntimeError("simulated failure")
    except RuntimeError:
        pass
    # Row should NOT be present after rollback
    with connect(temp_paths.db_path) as conn:
        row = conn.execute(
            "SELECT record_id FROM capture_records WHERE record_id='rollback-1'"
        ).fetchone()
    assert row is None


def test_managed_connection_does_not_suppress_exception(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with pytest.raises(ValueError, match="intentional"):
        with connect(temp_paths.db_path):
            raise ValueError("intentional")


def test_connect_returns_managed_connection_with_expected_pragmas(temp_paths) -> None:
    conn = connect(temp_paths.db_path)
    try:
        assert isinstance(conn, ManagedConnection)
        assert conn.row_factory is sqlite3.Row
        busy_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    finally:
        conn.close()

    assert busy_timeout == 30000
    assert str(journal_mode).lower() == "wal"


# ---------------------------------------------------------------------------
# _ensure_column — ADD COLUMN path
# ---------------------------------------------------------------------------


def test_ensure_column_adds_missing_column(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        # Verify the column doesn't exist yet (use a truly novel name)
        rows = conn.execute("PRAGMA table_info(capture_records)").fetchall()
        names = [row["name"] for row in rows]
        assert "novel_test_col" not in names

        _ensure_column(conn, "capture_records", "novel_test_col", "TEXT NULL")
        conn.commit()

        rows = conn.execute("PRAGMA table_info(capture_records)").fetchall()
        names = [row["name"] for row in rows]
        assert "novel_test_col" in names


def test_ensure_column_is_idempotent(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        # Call twice — should not raise
        _ensure_column(conn, "capture_records", "archived", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "capture_records", "archived", "INTEGER NOT NULL DEFAULT 0")


# ---------------------------------------------------------------------------
# ensure_database — idempotency
# ---------------------------------------------------------------------------


def test_ensure_database_is_idempotent(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    ensure_database(temp_paths.db_path)  # Second call must not raise
    assert temp_paths.db_path.exists()


def test_ensure_database_creates_all_indexes(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        indexes = {
            row[1]
            for row in conn.execute(
                "SELECT * FROM sqlite_master WHERE type='index' AND tbl_name='capture_records'"
            ).fetchall()
        }
    assert "idx_capture_records_planned_local_ts" in indexes
    assert "idx_capture_records_outcome_category" in indexes
