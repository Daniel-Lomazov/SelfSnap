from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

from selfsnap.models import AppConfig
from selfsnap.records import get_retention_candidates, mark_retention_deleted


@dataclass(slots=True)
class RetentionAction:
    record_id: str
    image_path: str
    deleted: bool


def apply_retention(
    connection: sqlite3.Connection, config: AppConfig, now_utc: datetime | None = None
) -> list[RetentionAction]:
    if config.retention_mode != "keep_days" or config.retention_days is None:
        return []
    now_utc = now_utc or datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(days=config.retention_days)
    actions: list[RetentionAction] = []
    for record in get_retention_candidates(connection, cutoff.isoformat()):
        deleted = False
        if record.image_path:
            file_path = Path(record.image_path)
            if file_path.exists():
                file_path.unlink()
                deleted = True
            mark_retention_deleted(connection, record.record_id, now_utc.isoformat())
            actions.append(
                RetentionAction(record_id=record.record_id, image_path=record.image_path, deleted=deleted)
            )
    return actions

