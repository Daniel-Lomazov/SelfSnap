"""Tests for apply_purge and apply_retention_and_purge in selfsnap.retention."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from selfsnap.db import connect, ensure_database
from selfsnap.models import AppConfig, CaptureRecord
from selfsnap.records import insert_capture_record, mark_record_archived
from selfsnap.retention import apply_purge, apply_retention, apply_retention_and_purge


def _make_record(
    record_id: str = "r1",
    image_path: str | None = None,
    file_present: bool = True,
    archived: bool = False,
    archived_at_utc: str | None = None,
    finished_utc: str | None = None,
) -> CaptureRecord:
    now = datetime.now(UTC).isoformat()
    return CaptureRecord(
        record_id=record_id,
        trigger_source="manual",
        schedule_id=None,
        planned_local_ts=None,
        started_utc=now,
        finished_utc=finished_utc or now,
        outcome_category="success",
        outcome_code="capture_saved",
        image_path=image_path,
        file_present=file_present,
        image_sha256="abc",
        monitor_count=1,
        composite_width=1920,
        composite_height=1080,
        file_bytes=100,
        error_code=None,
        error_message=None,
        archived=archived,
        archived_at_utc=archived_at_utc,
        retention_deleted_at_utc=None,
        app_version="1.0.1",
        created_utc=now,
    )


def _keep_days_config(temp_paths, days: int = 1, purge: bool = True, grace_days: int = 1) -> AppConfig:
    return AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
        retention_mode="keep_days",
        retention_days=days,
        purge_enabled=purge,
        retention_grace_days=grace_days,
    )


# ---------------------------------------------------------------------------
# apply_purge — gate conditions
# ---------------------------------------------------------------------------

def test_apply_purge_returns_empty_when_purge_disabled(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    config = _keep_days_config(temp_paths, purge=False)
    with connect(temp_paths.db_path) as conn:
        actions = apply_purge(conn, config)
    assert actions == []


def test_apply_purge_returns_empty_when_retention_mode_is_keep_forever(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
        retention_mode="keep_forever",
        purge_enabled=True,
    )
    with connect(temp_paths.db_path) as conn:
        actions = apply_purge(conn, config)
    assert actions == []


# ---------------------------------------------------------------------------
# apply_purge — deletes file and marks record
# ---------------------------------------------------------------------------

def test_apply_purge_deletes_archived_file_past_grace(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    # Create a real file to be purged
    archived_file = temp_paths.default_archive_root / "archive.png"
    archived_file.parent.mkdir(parents=True, exist_ok=True)
    archived_file.write_bytes(b"archived-data")

    old_archived_at = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    rec = _make_record(record_id="r1", image_path=str(archived_file), archived=True, archived_at_utc=old_archived_at)
    config = _keep_days_config(temp_paths, grace_days=2)

    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, rec)
        # Manually set archived=1 and archived_at_utc in DB (insert_capture_record inserts archived=0 by default)
        conn.execute(
            "UPDATE capture_records SET archived=1, archived_at_utc=? WHERE record_id=?",
            (old_archived_at, rec.record_id),
        )
        conn.commit()
        actions = apply_purge(conn, config, now_utc=datetime.now(UTC))

    assert len(actions) == 1
    assert actions[0].deleted is True
    assert not archived_file.exists()


def test_apply_purge_handles_missing_file_gracefully(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    old_archived_at = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    # File path doesn't exist
    rec = _make_record(
        record_id="r1",
        image_path="/nonexistent/archive.png",
        archived=True,
        archived_at_utc=old_archived_at,
    )
    config = _keep_days_config(temp_paths, grace_days=2)

    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, rec)
        conn.execute(
            "UPDATE capture_records SET archived=1, archived_at_utc=? WHERE record_id=?",
            (old_archived_at, rec.record_id),
        )
        conn.commit()
        actions = apply_purge(conn, config, now_utc=datetime.now(UTC))

    # The purge should still mark the record, but deleted=True because unlink(missing_ok=True)
    assert len(actions) == 1


def test_apply_purge_returns_empty_for_no_candidates(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    config = _keep_days_config(temp_paths, purge=True)
    with connect(temp_paths.db_path) as conn:
        actions = apply_purge(conn, config, now_utc=datetime.now(UTC))
    assert actions == []


# ---------------------------------------------------------------------------
# apply_retention — keep_forever skips archiving
# ---------------------------------------------------------------------------

def test_apply_retention_returns_empty_for_keep_forever(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
        retention_mode="keep_forever",
    )
    old_file = temp_paths.default_capture_root / "old.png"
    old_file.parent.mkdir(parents=True, exist_ok=True)
    old_file.write_bytes(b"data")
    old_time = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, _make_record(record_id="r1", image_path=str(old_file), finished_utc=old_time))
        actions = apply_retention(conn, config, paths=temp_paths)
    assert actions == []
    assert old_file.exists()  # file not touched


def test_apply_retention_skips_records_with_no_image_path(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
        retention_mode="keep_days",
        retention_days=1,
    )
    old_time = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, _make_record(record_id="r1", image_path=None, finished_utc=old_time))
        actions = apply_retention(conn, config, paths=temp_paths, now_utc=datetime.now(UTC))
    assert actions == []


def test_apply_retention_skips_files_that_do_not_exist(temp_paths) -> None:
    """Record points to a missing file — archived flag should still be set but archived=False."""
    ensure_database(temp_paths.db_path)
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
        retention_mode="keep_days",
        retention_days=1,
    )
    old_time = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    missing_path = str(temp_paths.default_capture_root / "missing.png")
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, _make_record(record_id="r1", image_path=missing_path, finished_utc=old_time))
        actions = apply_retention(conn, config, paths=temp_paths, now_utc=datetime.now(UTC))
    assert len(actions) == 1
    assert actions[0].archived is False  # file didn't exist, so wasn't moved


# ---------------------------------------------------------------------------
# apply_retention_and_purge — combined pipeline
# ---------------------------------------------------------------------------

def test_apply_retention_and_purge_returns_both_action_lists(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    config = _keep_days_config(temp_paths, days=1, purge=True, grace_days=1)
    with connect(temp_paths.db_path) as conn:
        ret_actions, purge_actions = apply_retention_and_purge(
            conn, config, now_utc=datetime.now(UTC), paths=temp_paths
        )
    assert isinstance(ret_actions, list)
    assert isinstance(purge_actions, list)
