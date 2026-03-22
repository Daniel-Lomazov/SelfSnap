from __future__ import annotations

from pathlib import Path

import pytest

from selfsnap.paths import AppPaths


Path("tests/.tmp").mkdir(parents=True, exist_ok=True)


@pytest.fixture
def temp_paths(tmp_path: Path) -> AppPaths:
    root = tmp_path / "AppData" / "Local" / "SelfSnap"
    pictures_root = tmp_path / "Pictures" / "SelfSnap"
    return AppPaths(
        root=root,
        config_dir=root / "config",
        data_dir=root / "data",
        logs_dir=root / "logs",
        default_capture_root=pictures_root / "captures",
        default_archive_root=pictures_root / "archive",
        bin_dir=root / "bin",
        config_path=root / "config" / "config.json",
        db_path=root / "data" / "selfsnap.db",
        log_path=root / "logs" / "selfsnap.log",
    )
