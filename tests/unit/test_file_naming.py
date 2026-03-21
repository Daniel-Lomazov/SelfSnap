from __future__ import annotations

from datetime import datetime
from pathlib import Path

from selfsnap.models import AppConfig, TriggerSource


def test_capture_file_path_uses_expected_format(temp_paths) -> None:
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
    )
    path = temp_paths.capture_file_path(
        temp_paths.resolve_capture_root(config),
        datetime(2026, 3, 21, 14, 0, 0),
        TriggerSource.SCHEDULED,
        "afternoon",
    )
    assert path.name == "cap_2026-03-21_14-00-00_scheduled_afternoon.png"


def test_archive_file_path_preserves_relative_structure(temp_paths) -> None:
    capture_root = temp_paths.default_capture_root
    archive_root = temp_paths.default_archive_root
    source = capture_root / "2026" / "03" / "21" / "cap_2026-03-21_14-00-00_scheduled_afternoon.png"
    archived = temp_paths.archive_file_path(
        archive_root=archive_root,
        capture_root=capture_root,
        source_path=source,
        archived_at_local=datetime(2026, 3, 22, 10, 30, 0),
    )
    assert archived == archive_root / "2026" / "03" / "21" / source.name


def test_archive_file_path_renames_on_collision(temp_paths) -> None:
    capture_root = temp_paths.default_capture_root
    archive_root = temp_paths.default_archive_root
    source = capture_root / "cap.png"
    existing = archive_root / "cap.png"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_bytes(b"collision")

    archived = temp_paths.archive_file_path(
        archive_root=archive_root,
        capture_root=capture_root,
        source_path=source,
        archived_at_local=datetime(2026, 3, 22, 10, 30, 0),
    )

    assert archived == Path(str(existing.with_name("cap_2026-03-22_10-30-00.png")))
