from __future__ import annotations

from datetime import datetime, timedelta, timezone

from selfsnap.db import connect, ensure_database
from selfsnap.models import AppConfig, CaptureRecord
from selfsnap.records import insert_capture_record
from selfsnap.retention import apply_retention


def test_apply_retention_moves_old_files_into_archive_and_marks_db(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    temp_paths.ensure_dirs()
    old_file = temp_paths.default_capture_root / "2026" / "03" / "20" / "old.png"
    old_file.parent.mkdir(parents=True, exist_ok=True)
    old_file.write_bytes(b"old-data")
    archive_root = temp_paths.default_archive_root
    old_time = datetime.now(timezone.utc) - timedelta(days=5)

    record = CaptureRecord(
        record_id="record-1",
        trigger_source="manual",
        schedule_id=None,
        planned_local_ts=None,
        started_utc=old_time.isoformat(),
        finished_utc=old_time.isoformat(),
        outcome_category="success",
        outcome_code="capture_saved",
        image_path=str(old_file),
        file_present=True,
        image_sha256="abc",
        monitor_count=1,
        composite_width=100,
        composite_height=100,
        file_bytes=8,
        error_code=None,
        error_message=None,
        archived=False,
        archived_at_utc=None,
        retention_deleted_at_utc=None,
        app_version="0.1.0",
        created_utc=old_time.isoformat(),
    )

    with connect(temp_paths.db_path) as connection:
        insert_capture_record(connection, record)
        actions = apply_retention(
            connection,
            AppConfig(
                capture_storage_root=str(temp_paths.default_capture_root),
                archive_storage_root=str(archive_root),
                retention_mode="keep_days",
                retention_days=1,
            ),
            paths=temp_paths,
            now_utc=datetime.now(timezone.utc),
        )
        row = connection.execute(
            "SELECT image_path, archived, archived_at_utc, file_present FROM capture_records WHERE record_id = ?",
            (record.record_id,),
        ).fetchone()

    assert len(actions) == 1
    assert not old_file.exists()
    archived_path = archive_root / "2026" / "03" / "20" / "old.png"
    assert archived_path.exists()
    assert row["image_path"] == str(archived_path)
    assert row["archived"] == 1
    assert row["archived_at_utc"] is not None
    assert row["file_present"] == 1
