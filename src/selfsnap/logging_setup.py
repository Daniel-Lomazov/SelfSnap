from __future__ import annotations

from logging import Formatter, Logger, getLogger
import logging
from logging.handlers import RotatingFileHandler
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
    handler = RotatingFileHandler(paths.log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    formatter = UtcFormatter("%(asctime)sZ %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger

