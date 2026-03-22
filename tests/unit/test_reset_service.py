from __future__ import annotations

from datetime import datetime, timezone

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.db import connect, ensure_database
from selfsnap.models import CaptureRecord, StoragePreset
from selfsnap.records import insert_capture_record
from selfsnap.reset_service import perform_clean_reset


def test_perform_clean_reset_removes_user_state_and_relaunches(temp_paths, monkeypatch) -> None:
    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.app_enabled = True
    save_config(temp_paths, config)

    ensure_database(temp_paths.db_path)
    capture_file = temp_paths.default_capture_root / "2026" / "03" / "22" / "cap_2026-03-22_10-00-00_manual_manual.png"
    archive_file = temp_paths.default_archive_root / "2026" / "03" / "21" / "cap_2026-03-21_09-00-00_manual_manual.png"
    capture_file.parent.mkdir(parents=True, exist_ok=True)
    archive_file.parent.mkdir(parents=True, exist_ok=True)
    capture_file.write_bytes(b"capture")
    archive_file.write_bytes(b"archive")
    temp_paths.log_path.parent.mkdir(parents=True, exist_ok=True)
    temp_paths.log_path.write_text("log", encoding="utf-8")

    record = CaptureRecord(
        record_id="record-1",
        trigger_source="manual",
        schedule_id=None,
        planned_local_ts=None,
        started_utc=datetime.now(timezone.utc).isoformat(),
        finished_utc=datetime.now(timezone.utc).isoformat(),
        outcome_category="success",
        outcome_code="capture_saved",
        image_path=str(capture_file),
        file_present=True,
        image_sha256="abc",
        monitor_count=1,
        composite_width=100,
        composite_height=100,
        file_bytes=7,
        error_code=None,
        error_message=None,
        archived=False,
        archived_at_utc=None,
        retention_deleted_at_utc=None,
        app_version="0.1.0",
        created_utc=datetime.now(timezone.utc).isoformat(),
    )
    with connect(temp_paths.db_path) as connection:
        insert_capture_record(connection, record)

    launch_calls: list[list[str]] = []
    monkeypatch.setattr("selfsnap.reset_service.delete_all_selfsnap_tasks", lambda logger=None: ["task-1"])
    monkeypatch.setattr("selfsnap.reset_service.remove_startup_shortcut", lambda: None)
    class RunningProcess:
        def poll(self):
            return None
    monkeypatch.setattr(
        "selfsnap.reset_service.launch_background",
        lambda spec: launch_calls.append(spec.command()) or RunningProcess(),
    )

    summary = perform_clean_reset(temp_paths)

    assert summary.deleted_tasks == 1
    assert summary.relaunched is True
    assert launch_calls
    assert not temp_paths.config_dir.exists()
    assert not temp_paths.data_dir.exists()
    assert not temp_paths.logs_dir.exists()
    assert not capture_file.exists()
    assert not archive_file.exists()


def test_perform_clean_reset_preserves_non_selfsnap_files_in_custom_roots(temp_paths, monkeypatch) -> None:
    custom_capture_root = temp_paths.user_profile / "Desktop" / "MixedFolder"
    custom_archive_root = temp_paths.user_profile / "Desktop" / "MixedArchive"
    capture_file = custom_capture_root / "2026" / "03" / "23" / "cap_2026-03-23_10-00-00_manual_manual.png"
    archive_file = custom_archive_root / "2026" / "03" / "22" / "cap_2026-03-22_10-00-00_manual_manual.png"
    unrelated_capture_file = custom_capture_root / "notes.txt"
    unrelated_archive_file = custom_archive_root / "keep.me"
    capture_file.parent.mkdir(parents=True, exist_ok=True)
    archive_file.parent.mkdir(parents=True, exist_ok=True)
    unrelated_capture_file.write_text("keep", encoding="utf-8")
    unrelated_archive_file.write_text("keep", encoding="utf-8")
    capture_file.write_bytes(b"capture")
    archive_file.write_bytes(b"archive")

    config = load_or_create_config(temp_paths)
    config.first_run_completed = True
    config.storage_preset = StoragePreset.CUSTOM.value
    config.capture_storage_root = str(custom_capture_root)
    config.archive_storage_root = str(custom_archive_root)
    save_config(temp_paths, config)

    ensure_database(temp_paths.db_path)
    record = CaptureRecord(
        record_id="record-2",
        trigger_source="manual",
        schedule_id=None,
        planned_local_ts=None,
        started_utc=datetime.now(timezone.utc).isoformat(),
        finished_utc=datetime.now(timezone.utc).isoformat(),
        outcome_category="success",
        outcome_code="capture_saved",
        image_path=str(capture_file),
        file_present=True,
        image_sha256="def",
        monitor_count=1,
        composite_width=100,
        composite_height=100,
        file_bytes=7,
        error_code=None,
        error_message=None,
        archived=False,
        archived_at_utc=None,
        retention_deleted_at_utc=None,
        app_version="0.1.0",
        created_utc=datetime.now(timezone.utc).isoformat(),
    )
    with connect(temp_paths.db_path) as connection:
        insert_capture_record(connection, record)

    monkeypatch.setattr("selfsnap.reset_service.delete_all_selfsnap_tasks", lambda logger=None: [])
    monkeypatch.setattr("selfsnap.reset_service.remove_startup_shortcut", lambda: None)
    monkeypatch.setattr("selfsnap.reset_service.launch_background", lambda spec: None)

    perform_clean_reset(temp_paths)

    assert not capture_file.exists()
    assert unrelated_capture_file.exists()
    assert unrelated_archive_file.exists()


def test_perform_clean_reset_removes_owned_storage_trees(temp_paths, monkeypatch) -> None:
    owned_capture_note = temp_paths.default_capture_root / "notes.txt"
    owned_archive_note = temp_paths.default_archive_root / "keep.me"
    owned_capture_note.parent.mkdir(parents=True, exist_ok=True)
    owned_archive_note.parent.mkdir(parents=True, exist_ok=True)
    owned_capture_note.write_text("owned", encoding="utf-8")
    owned_archive_note.write_text("owned", encoding="utf-8")

    monkeypatch.setattr("selfsnap.reset_service.delete_all_selfsnap_tasks", lambda logger=None: [])
    monkeypatch.setattr("selfsnap.reset_service.remove_startup_shortcut", lambda: None)
    monkeypatch.setattr("selfsnap.reset_service.launch_background", lambda spec: None)

    perform_clean_reset(temp_paths)

    assert not temp_paths.default_capture_root.exists()
    assert not temp_paths.default_archive_root.exists()
