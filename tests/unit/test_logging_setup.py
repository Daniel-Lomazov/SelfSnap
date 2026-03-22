from __future__ import annotations

import logging
from pathlib import Path

from selfsnap.logging_setup import setup_logging


class FakeHandler(logging.Handler):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.baseFilename = str(path)

    def emit(self, record) -> None:
        return None


def test_setup_logging_falls_back_to_pid_log_when_primary_is_locked(temp_paths, monkeypatch) -> None:
    logger = logging.getLogger("selfsnap")
    logger.handlers.clear()

    created_paths: list[Path] = []

    def fake_rotating_file_handler(path, *args, **kwargs):
        path = Path(path)
        created_paths.append(path)
        if path == temp_paths.log_path:
            raise PermissionError("locked")
        return FakeHandler(path)

    monkeypatch.setattr("selfsnap.logging_setup.RotatingFileHandler", fake_rotating_file_handler)

    resolved_logger = setup_logging(temp_paths)

    assert resolved_logger.handlers
    assert created_paths[0] == temp_paths.log_path
    assert created_paths[1].parent == temp_paths.logs_dir
    assert created_paths[1].name.startswith("selfsnap.")
    assert created_paths[1].suffix == ".log"

    resolved_logger.handlers.clear()
