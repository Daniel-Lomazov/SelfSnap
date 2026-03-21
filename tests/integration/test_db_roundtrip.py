from __future__ import annotations

from selfsnap.db import connect, ensure_database
from selfsnap.models import CaptureRecord
from selfsnap.records import get_latest_record, insert_capture_record


def test_insert_and_fetch_latest_record(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    record = CaptureRecord(
        record_id="record-1",
        trigger_source="manual",
        schedule_id=None,
        planned_local_ts=None,
        started_utc="2026-03-21T10:00:00+00:00",
        finished_utc="2026-03-21T10:00:01+00:00",
        outcome_category="success",
        outcome_code="capture_saved",
        image_path="C:\\capture.png",
        file_present=True,
        image_sha256="abc",
        monitor_count=1,
        composite_width=100,
        composite_height=100,
        file_bytes=123,
        error_code=None,
        error_message=None,
        archived=False,
        archived_at_utc=None,
        retention_deleted_at_utc=None,
        app_version="0.1.0",
        created_utc="2026-03-21T10:00:01+00:00",
    )
    with connect(temp_paths.db_path) as connection:
        insert_capture_record(connection, record)
        latest = get_latest_record(connection)
    assert latest is not None
    assert latest.record_id == "record-1"
    assert latest.archived is False
    assert latest.archived_at_utc is None
