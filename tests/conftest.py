from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from selfsnap.paths import AppPaths


def pytest_configure(config) -> None:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        local_appdata = str(Path.home() / "AppData" / "Local")
    base_root = Path(local_appdata) / "SelfSnap" / "pytest" / "tmp"
    base_root.mkdir(parents=True, exist_ok=True)
    config.option.basetemp = tempfile.mkdtemp(prefix="run-", dir=base_root)


@pytest.fixture
def temp_paths(tmp_path: Path) -> AppPaths:
    root = tmp_path / "AppData" / "Local" / "SelfSnap"
    pictures_root = tmp_path / "Pictures" / "SelfSnap"
    return AppPaths(
        user_profile=tmp_path,
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
