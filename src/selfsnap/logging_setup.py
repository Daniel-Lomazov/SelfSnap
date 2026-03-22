from __future__ import annotations

from logging import Formatter, Logger, getLogger
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import tempfile
import time

from selfsnap.paths import AppPaths


class UtcFormatter(Formatter):
    converter = time.gmtime


def setup_logging(paths: AppPaths, level: str = "INFO") -> Logger:
    paths.ensure_dirs()
    logger = getLogger("selfsnap")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if logger.handlers:
        return logger
    handler, selected_path = _build_handler(paths)
    formatter = UtcFormatter("%(asctime)sZ %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    if selected_path is not None and selected_path != paths.log_path:
        logger.warning("Primary log file was locked; using fallback log file %s", selected_path)
    return logger


def _build_handler(paths: AppPaths) -> tuple[logging.Handler, Path | None]:
    candidate_paths = [
        paths.log_path,
        paths.logs_dir / f"selfsnap.{os.getpid()}.log",
    ]
    temp_logs_dir = Path(tempfile.gettempdir()) / "SelfSnap" / "logs"
    temp_logs_dir.mkdir(parents=True, exist_ok=True)
    candidate_paths.append(temp_logs_dir / f"selfsnap.{os.getpid()}.log")

    for candidate in candidate_paths:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                candidate,
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            return handler, candidate
        except PermissionError:
            continue
    return logging.NullHandler(), None
