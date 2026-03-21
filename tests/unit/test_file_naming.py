from __future__ import annotations

from datetime import datetime

from selfsnap.models import AppConfig, TriggerSource


def test_capture_file_path_uses_expected_format(temp_paths) -> None:
    config = AppConfig(capture_storage_root=str(temp_paths.default_capture_root))
    path = temp_paths.capture_file_path(
        temp_paths.resolve_capture_root(config),
        datetime(2026, 3, 21, 14, 0, 0),
        TriggerSource.SCHEDULED,
        "afternoon",
    )
    assert path.name == "cap_2026-03-21_14-00-00_scheduled_afternoon.png"

