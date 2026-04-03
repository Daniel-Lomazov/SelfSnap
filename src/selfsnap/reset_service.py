from __future__ import annotations

import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from selfsnap.config_store import default_config, load_or_create_config
from selfsnap.db import connect, ensure_database
from selfsnap.models import ConfigValidationError
from selfsnap.paths import AppPaths
from selfsnap.records import clear_capture_history, list_all_record_paths
from selfsnap.runtime_launch import launch_background, resolve_tray_background_invocation
from selfsnap.scheduler.task_scheduler import delete_all_selfsnap_tasks
from selfsnap.storage import normalize_storage_config
from selfsnap.tray.startup import remove_startup_shortcut


@dataclass(slots=True)
class ResetSummary:
    deleted_files: int
    deleted_directories: int
    deleted_tasks: int
    relaunched: bool


def perform_clean_reset(paths: AppPaths, logger: logging.Logger | None = None) -> ResetSummary:
    logger = logger or logging.getLogger("selfsnap")
    try:
        config = normalize_storage_config(paths, load_or_create_config(paths))
    except ConfigValidationError:
        config = default_config(paths)

    capture_root = paths.resolve_capture_root(config)
    archive_root = paths.resolve_archive_root(config)

    ensure_database(paths.db_path)
    connection = connect(paths.db_path)
    try:
        file_paths = set(list_all_record_paths(connection))
        clear_capture_history(connection)
    finally:
        connection.close()

    deleted_files = 0
    deleted_directories = 0
    deleted_tasks = len(delete_all_selfsnap_tasks(logger))
    remove_startup_shortcut()

    for directory in _owned_storage_directories(paths, capture_root, archive_root):
        if directory.exists():
            deleted_files += _count_files(directory)
            _remove_tree(directory)
            deleted_directories += 1

    for candidate in _iter_managed_files(capture_root, archive_root, file_paths):
        if candidate.exists() and candidate.is_file():
            candidate.unlink()
            deleted_files += 1

    for directory in _custom_storage_directories(paths, capture_root, archive_root):
        if directory.exists():
            deleted_files += _delete_matching_capture_files(directory)
            deleted_directories += _remove_empty_dirs(directory)

    for app_dir in (paths.config_dir, paths.data_dir, paths.logs_dir):
        if app_dir.exists():
            _remove_tree(app_dir)
            deleted_directories += 1

    process = launch_background(resolve_tray_background_invocation(paths))
    relaunched = _wait_for_background_launch(process)
    return ResetSummary(
        deleted_files=deleted_files,
        deleted_directories=deleted_directories,
        deleted_tasks=deleted_tasks,
        relaunched=relaunched,
    )


def _iter_managed_files(
    capture_root: Path, archive_root: Path, record_paths: set[Path]
) -> set[Path]:
    managed = {
        path
        for path in record_paths
        if _is_relative_to(path, capture_root) or _is_relative_to(path, archive_root)
    }
    for root in _managed_directories(capture_root, archive_root):
        if not root.exists():
            continue
        for file_path in root.rglob("cap_*.png"):
            if file_path.is_file():
                managed.add(file_path)
    return managed


def _managed_directories(capture_root: Path, archive_root: Path) -> tuple[Path, Path]:
    return capture_root, archive_root


def _owned_storage_directories(
    paths: AppPaths, capture_root: Path, archive_root: Path
) -> tuple[Path, ...]:
    owned_roots = {
        paths.default_capture_root.resolve(),
        paths.default_archive_root.resolve(),
        paths.onedrive_capture_root().resolve(),
        paths.onedrive_archive_root().resolve(),
    }
    candidates: list[Path] = []
    for root in _managed_directories(capture_root, archive_root):
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if resolved in owned_roots:
            candidates.append(root)
    return tuple(candidates)


def _custom_storage_directories(
    paths: AppPaths, capture_root: Path, archive_root: Path
) -> tuple[Path, ...]:
    owned = {
        path.resolve() for path in _owned_storage_directories(paths, capture_root, archive_root)
    }
    candidates: list[Path] = []
    for root in _managed_directories(capture_root, archive_root):
        try:
            resolved = root.resolve()
        except OSError:
            resolved = root
        if resolved not in owned:
            candidates.append(root)
    return tuple(candidates)


def _delete_matching_capture_files(root: Path) -> int:
    deleted = 0
    for file_path in root.rglob("cap_*.png"):
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            deleted += 1
    return deleted


def _remove_empty_dirs(root: Path) -> int:
    removed = 0
    for directory in sorted((path for path in root.rglob("*") if path.is_dir()), reverse=True):
        try:
            directory.rmdir()
            removed += 1
        except OSError:
            continue
    try:
        root.rmdir()
        removed += 1
    except OSError:
        pass
    return removed


def _remove_tree(root: Path) -> None:
    shutil.rmtree(root, ignore_errors=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _count_files(root: Path) -> int:
    return sum(1 for path in root.rglob("*") if path.is_file())


def _wait_for_background_launch(process) -> bool:
    if process is None:
        return False
    poll = getattr(process, "poll", None)
    if poll is None:
        return True
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if poll() is not None:
            return False
        time.sleep(0.2)
    return poll() is None
