from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path

from selfsnap.models import AppConfig, TriggerSource


APP_DIR_NAME = "SelfSnap"


@dataclass(slots=True)
class AppPaths:
    root: Path
    config_dir: Path
    data_dir: Path
    logs_dir: Path
    default_capture_root: Path
    config_path: Path
    db_path: Path
    log_path: Path

    def ensure_dirs(self) -> None:
        for directory in (
            self.root,
            self.config_dir,
            self.data_dir,
            self.logs_dir,
            self.default_capture_root,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def resolve_capture_root(self, config: AppConfig) -> Path:
        expanded = os.path.expandvars(config.capture_storage_root)
        return Path(expanded).expanduser()

    def capture_file_path(
        self,
        capture_root: Path,
        when_local: datetime,
        trigger_source: TriggerSource,
        schedule_id: str | None,
    ) -> Path:
        folder = capture_root / when_local.strftime("%Y") / when_local.strftime("%m") / when_local.strftime("%d")
        suffix = schedule_id if schedule_id else "manual"
        filename = f"cap_{when_local.strftime('%Y-%m-%d_%H-%M-%S')}_{trigger_source.value}_{suffix}.png"
        return folder / filename


def resolve_app_paths() -> AppPaths:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        local_appdata = str(Path.home() / "AppData" / "Local")
    root = Path(local_appdata) / APP_DIR_NAME
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

