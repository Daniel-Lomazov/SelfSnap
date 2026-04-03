from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from selfsnap.models import AppConfig, TriggerSource

APP_DIR_NAME = "SelfSnap"


@dataclass(slots=True)
class AppPaths:
    user_profile: Path
    root: Path
    config_dir: Path
    data_dir: Path
    logs_dir: Path
    default_capture_root: Path
    default_archive_root: Path
    bin_dir: Path
    config_path: Path
    db_path: Path
    log_path: Path

    def ensure_dirs(self) -> None:
        for directory in (
            self.root,
            self.config_dir,
            self.data_dir,
            self.logs_dir,
            self.bin_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def preferred_onedrive_root(self) -> Path:
        onedrive = os.environ.get("OneDrive")
        if onedrive:
            return Path(onedrive)
        return self.user_profile / "OneDrive"

    def onedrive_capture_root(self) -> Path:
        return self.preferred_onedrive_root() / "Pictures" / APP_DIR_NAME / "captures"

    def onedrive_archive_root(self) -> Path:
        return self.preferred_onedrive_root() / "Pictures" / APP_DIR_NAME / "archive"

    def resolve_capture_root(self, config: AppConfig) -> Path:
        expanded = os.path.expandvars(config.capture_storage_root)
        return Path(expanded).expanduser()

    def resolve_archive_root(self, config: AppConfig) -> Path:
        expanded = os.path.expandvars(config.archive_storage_root)
        return Path(expanded).expanduser()

    def capture_file_path(
        self,
        capture_root: Path,
        when_local: datetime,
        trigger_source: TriggerSource,
        schedule_id: str | None,
    ) -> Path:
        folder = (
            capture_root
            / when_local.strftime("%Y")
            / when_local.strftime("%m")
            / when_local.strftime("%d")
        )
        suffix = schedule_id if schedule_id else "manual"
        filename = (
            f"cap_{when_local.strftime('%Y-%m-%d_%H-%M-%S')}_{trigger_source.value}_{suffix}.png"
        )
        return folder / filename

    def archive_file_path(
        self,
        archive_root: Path,
        capture_root: Path,
        source_path: Path,
        archived_at_local: datetime,
    ) -> Path:
        try:
            relative = source_path.relative_to(capture_root)
        except ValueError:
            relative = Path(source_path.name)
        destination = archive_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            return destination
        stem = destination.stem
        suffix = destination.suffix
        collision_name = f"{stem}_{archived_at_local.strftime('%Y-%m-%d_%H-%M-%S')}{suffix}"
        return destination.with_name(collision_name)


def resolve_app_paths() -> AppPaths:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        local_appdata = str(Path.home() / "AppData" / "Local")
    user_profile = os.environ.get("USERPROFILE")
    if not user_profile:
        user_profile = str(Path.home())
    root = Path(local_appdata) / APP_DIR_NAME
    pictures_root = Path(user_profile) / "Pictures" / APP_DIR_NAME
    return AppPaths(
        user_profile=Path(user_profile),
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
