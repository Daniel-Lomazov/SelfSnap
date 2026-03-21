from __future__ import annotations

from pathlib import Path

import pytest

from selfsnap.paths import AppPaths


@pytest.fixture
def temp_paths(tmp_path: Path) -> AppPaths:
    root = tmp_path / "SelfSnap"
    return AppPaths(
        root=root,
        config_dir=root / "config",
        data_dir=root / "data",
        logs_dir=root / "logs",
        default_capture_root=root / "captures",
        config_path=root / "config" / "config.json",
        db_path=root / "data" / "selfsnap.db",
        log_path=root / "logs" / "selfsnap.log",
    )

