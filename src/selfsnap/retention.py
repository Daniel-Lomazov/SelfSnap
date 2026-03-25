from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import sqlite3

from selfsnap.models import AppConfig
from selfsnap.paths import AppPaths, resolve_app_paths
from selfsnap.records import get_purge_candidates, get_retention_candidates, mark_record_archived, mark_record_purged


@dataclass(slots=True)
class RetentionAction:
    record_id: str
    image_path: str
    archived_path: str
    archived: bool


def apply_retention(
    connection: sqlite3.Connection,
    config: AppConfig,
    now_utc: datetime | None = None,
    paths: AppPaths | None = None,
) -> list[RetentionAction]:
    if config.retention_mode != "keep_days" or config.retention_days is None:
        return []
    paths = paths or resolve_app_paths()
    now_utc = now_utc or datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(days=config.retention_days)
    actions: list[RetentionAction] = []
    capture_root = paths.resolve_capture_root(config)
    archive_root = paths.resolve_archive_root(config)
    for record in get_retention_candidates(connection, cutoff.isoformat()):
        if record.image_path:
            file_path = Path(record.image_path)
            archived_path = paths.archive_file_path(
                archive_root=archive_root,
                capture_root=capture_root,
                source_path=file_path,
                archived_at_local=now_utc.astimezone(),
            )
            archived = False
            if file_path.exists():
                archived_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(archived_path))
                archived = True
            mark_record_archived(connection, record.record_id, str(archived_path), now_utc.isoformat())
            actions.append(
                RetentionAction(
                    record_id=record.record_id,
                    image_path=record.image_path,
                    archived_path=str(archived_path),
                    archived=archived,
                )
            )
    return actions


@dataclass(slots=True)
class PurgeAction:
    record_id: str
    archived_path: str
    deleted: bool


def apply_purge(
    connection: sqlite3.Connection,
    config: AppConfig,
    now_utc: datetime | None = None,
) -> list[PurgeAction]:
    if not config.purge_enabled or config.retention_mode != "keep_days":
        return []
    now_utc = now_utc or datetime.now(timezone.utc)
    grace_cutoff = now_utc - timedelta(days=config.retention_grace_days)
    actions: list[PurgeAction] = []
    for record in get_purge_candidates(connection, grace_cutoff.isoformat()):
        deleted = False
        if record.image_path:
            Path(record.image_path).unlink(missing_ok=True)
            deleted = True
        mark_record_purged(connection, record.record_id, now_utc.isoformat())
        actions.append(
            PurgeAction(
                record_id=record.record_id,
                archived_path=record.image_path or "",
                deleted=deleted,
            )
        )
    return actions


def apply_retention_and_purge(
    connection: sqlite3.Connection,
    config: AppConfig,
    now_utc: datetime | None = None,
    paths: AppPaths | None = None,
) -> tuple[list[RetentionAction], list[PurgeAction]]:
    retention_actions = apply_retention(connection, config, now_utc=now_utc, paths=paths)
    purge_actions = apply_purge(connection, config, now_utc=now_utc)
    return retention_actions, purge_actions
