"""Tests for selfsnap.records — all DB query helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from selfsnap.db import connect, ensure_database
from selfsnap.models import CaptureRecord
from selfsnap.records import (
    clear_capture_history,
    daily_counts,
    get_by_schedule,
    get_latest_record,
    get_purge_candidates,
    get_recent,
    has_record_for_slot,
    insert_capture_record,
    list_all_record_paths,
    list_recent_records,
    mark_record_archived,
    mark_record_purged,
    resolve_latest_capture_path,
    summary_stats,
)


def _make_record(
    record_id: str = "r1",
    image_path: str | None = "/cap.png",
    file_present: bool = True,
    outcome_category: str = "success",
    outcome_code: str = "capture_saved",
    schedule_id: str | None = None,
    planned_local_ts: str | None = None,
    started_utc: str | None = None,
    finished_utc: str | None = None,
    archived: bool = False,
    archived_at_utc: str | None = None,
    file_bytes: int = 100,
) -> CaptureRecord:
    now = datetime.now(UTC).isoformat()
    return CaptureRecord(
        record_id=record_id,
        trigger_source="manual",
        schedule_id=schedule_id,
        planned_local_ts=planned_local_ts,
        started_utc=started_utc or now,
        finished_utc=finished_utc or now,
        outcome_category=outcome_category,
        outcome_code=outcome_code,
        image_path=image_path,
        file_present=file_present,
        image_sha256="abc",
        monitor_count=1,
        composite_width=1920,
        composite_height=1080,
        file_bytes=file_bytes,
        error_code=None,
        error_message=None,
        archived=archived,
        archived_at_utc=archived_at_utc,
        retention_deleted_at_utc=None,
        app_version="1.0.1",
        created_utc=now,
    )


# ---------------------------------------------------------------------------
# resolve_latest_capture_path
# ---------------------------------------------------------------------------


def test_resolve_latest_capture_path_returns_none_for_empty_db(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        result = resolve_latest_capture_path(conn)
    assert result is None


def test_resolve_latest_capture_path_returns_path_of_present_record(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, _make_record(image_path="/some/cap.png", file_present=True))
        result = resolve_latest_capture_path(conn)
    assert result is not None
    assert result.name == "cap.png"


def test_resolve_latest_capture_path_skips_absent_files(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(
            conn, _make_record(record_id="r1", image_path="/cap.png", file_present=False)
        )
        result = resolve_latest_capture_path(conn)
    assert result is None


# ---------------------------------------------------------------------------
# get_recent
# ---------------------------------------------------------------------------


def test_get_recent_returns_records_with_file_present(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, _make_record(record_id="r1", file_present=True))
        insert_capture_record(conn, _make_record(record_id="r2", file_present=False))
        results = get_recent(conn, n=10)
    assert len(results) == 1
    assert results[0].record_id == "r1"


def test_get_recent_respects_limit(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        for i in range(5):
            insert_capture_record(conn, _make_record(record_id=f"r{i}"))
        results = get_recent(conn, n=3)
    assert len(results) == 3


def test_get_recent_returns_empty_for_empty_db(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        assert get_recent(conn) == []


# ---------------------------------------------------------------------------
# summary_stats
# ---------------------------------------------------------------------------


def test_summary_stats_returns_zeros_for_empty_db(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        stats = summary_stats(conn)
    assert stats["total_captures"] == 0
    assert stats["total_bytes"] == 0


def test_summary_stats_counts_outcomes(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(
            conn, _make_record(record_id="r1", outcome_category="success", file_bytes=100)
        )
        insert_capture_record(
            conn, _make_record(record_id="r2", outcome_category="failed", file_bytes=0)
        )
        insert_capture_record(
            conn, _make_record(record_id="r3", outcome_category="skipped", file_bytes=0)
        )
        stats = summary_stats(conn)
    assert stats["total_captures"] == 3
    assert stats["total_success"] == 1
    assert stats["total_failed"] == 1
    assert stats["total_skipped"] == 1
    assert stats["total_bytes"] == 100


def test_summary_stats_counts_distinct_schedules(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, _make_record(record_id="r1", schedule_id="sched_a"))
        insert_capture_record(conn, _make_record(record_id="r2", schedule_id="sched_a"))
        insert_capture_record(conn, _make_record(record_id="r3", schedule_id="sched_b"))
        stats = summary_stats(conn)
    assert stats["distinct_schedules"] == 2


# ---------------------------------------------------------------------------
# daily_counts
# ---------------------------------------------------------------------------


def test_daily_counts_returns_today_entry(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    now_utc = datetime.now(UTC).isoformat()
    with connect(temp_paths.db_path) as conn:
        r = _make_record(started_utc=now_utc, finished_utc=now_utc)
        insert_capture_record(conn, r)
        counts = daily_counts(conn, days=7)
    assert len(counts) == 1
    assert counts[0][1] == 1  # count


def test_daily_counts_returns_empty_when_no_records(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        counts = daily_counts(conn, days=7)
    assert counts == []


# ---------------------------------------------------------------------------
# get_by_schedule
# ---------------------------------------------------------------------------


def test_get_by_schedule_returns_matching_records(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, _make_record(record_id="r1", schedule_id="sched_a"))
        insert_capture_record(conn, _make_record(record_id="r2", schedule_id="sched_b"))
        result = get_by_schedule(conn, "sched_a")
    assert len(result) == 1
    assert result[0].record_id == "r1"


def test_get_by_schedule_respects_limit(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        for i in range(10):
            insert_capture_record(conn, _make_record(record_id=f"r{i}", schedule_id="sched_a"))
        result = get_by_schedule(conn, "sched_a", limit=3)
    assert len(result) == 3


def test_get_by_schedule_returns_empty_for_unknown_schedule(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        result = get_by_schedule(conn, "no_such")
    assert result == []


# ---------------------------------------------------------------------------
# mark_record_purged / get_purge_candidates
# ---------------------------------------------------------------------------


def test_mark_record_purged_sets_purged_utc(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    now = datetime.now(UTC).isoformat()
    old_archived = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    with connect(temp_paths.db_path) as conn:
        rec = _make_record(archived=True, archived_at_utc=old_archived)
        insert_capture_record(conn, rec)
        mark_record_purged(conn, rec.record_id, now)
        row = conn.execute(
            "SELECT purged_utc, file_present FROM capture_records WHERE record_id = ?",
            (rec.record_id,),
        ).fetchone()
    assert row["purged_utc"] == now
    assert row["file_present"] == 0


def test_get_purge_candidates_returns_old_archived_records(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    old = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    future_cutoff = datetime.now(UTC).isoformat()
    with connect(temp_paths.db_path) as conn:
        rec = _make_record(archived=True, archived_at_utc=old)
        insert_capture_record(conn, rec)
        candidates = get_purge_candidates(conn, future_cutoff)
    assert len(candidates) == 1
    assert candidates[0].record_id == rec.record_id


def test_get_purge_candidates_excludes_already_purged(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    old = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    future_cutoff = datetime.now(UTC).isoformat()
    with connect(temp_paths.db_path) as conn:
        rec = _make_record(archived=True, archived_at_utc=old)
        insert_capture_record(conn, rec)
        mark_record_purged(conn, rec.record_id, old)
        candidates = get_purge_candidates(conn, future_cutoff)
    assert candidates == []


def test_get_purge_candidates_excludes_recent_archives(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    recent = datetime.now(UTC).isoformat()
    past_cutoff = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    with connect(temp_paths.db_path) as conn:
        rec = _make_record(archived=True, archived_at_utc=recent)
        insert_capture_record(conn, rec)
        candidates = get_purge_candidates(conn, past_cutoff)
    assert candidates == []


# ---------------------------------------------------------------------------
# list_all_record_paths
# ---------------------------------------------------------------------------


def test_list_all_record_paths_returns_distinct_paths(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, _make_record(record_id="r1", image_path="/a.png"))
        insert_capture_record(conn, _make_record(record_id="r2", image_path="/b.png"))
        insert_capture_record(conn, _make_record(record_id="r3", image_path=None))
        paths = list_all_record_paths(conn)
    path_names = {p.name for p in paths}
    assert path_names == {"a.png", "b.png"}


# ---------------------------------------------------------------------------
# clear_capture_history
# ---------------------------------------------------------------------------


def test_clear_capture_history_deletes_all_records(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        for i in range(3):
            insert_capture_record(conn, _make_record(record_id=f"r{i}"))
        clear_capture_history(conn)
        count = conn.execute("SELECT COUNT(*) FROM capture_records").fetchone()[0]
    assert count == 0


# ---------------------------------------------------------------------------
# list_recent_records
# ---------------------------------------------------------------------------


def test_list_recent_records_returns_all_record_types(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, _make_record(record_id="r1", file_present=True))
        insert_capture_record(conn, _make_record(record_id="r2", file_present=False))
        results = list_recent_records(conn, limit=10)
    assert len(results) == 2


def test_has_record_for_slot_returns_true_for_matching_slot(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    slot = "2026-04-01T09:00:00+00:00"
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(
            conn, _make_record(record_id="r1", schedule_id="sched_a", planned_local_ts=slot)
        )
        assert has_record_for_slot(conn, "sched_a", slot) is True


def test_has_record_for_slot_returns_false_for_different_schedule(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    slot = "2026-04-01T09:00:00+00:00"
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(
            conn, _make_record(record_id="r1", schedule_id="sched_a", planned_local_ts=slot)
        )
        assert has_record_for_slot(conn, "sched_b", slot) is False


def test_get_latest_record_returns_record_when_present(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        insert_capture_record(conn, _make_record(record_id="latest_r"))
        result = get_latest_record(conn)
    assert result is not None
    assert result.record_id == "latest_r"


def test_get_latest_record_returns_none_when_empty(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        result = get_latest_record(conn)
    assert result is None


def test_mark_record_archived_updates_row(temp_paths) -> None:
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as conn:
        rec = _make_record(record_id="arc_1", image_path="/some/path/cap.png")
        insert_capture_record(conn, rec)
        archived_at = datetime.now(UTC).isoformat()
        mark_record_archived(conn, "arc_1", "/archive/cap.png", archived_at)
        rows = conn.execute(
            "SELECT archived, image_path, archived_at_utc "
            "FROM capture_records WHERE record_id='arc_1'"
        ).fetchall()
    assert rows[0]["archived"] == 1
    assert rows[0]["image_path"] == "/archive/cap.png"
    assert rows[0]["archived_at_utc"] == archived_at
