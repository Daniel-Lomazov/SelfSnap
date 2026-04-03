from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from selfsnap.models import AppConfig
from selfsnap.paths import AppPaths
from selfsnap.runtime_launch import resolve_tray_background_invocation

SHORTCUT_NAME = "SelfSnap Win11.lnk"


@dataclass(slots=True)
class ShortcutSpec:
    target: str
    arguments: str
    working_directory: str


def startup_shortcut_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        appdata = str(Path.home() / "AppData" / "Roaming")
    return (
        Path(appdata)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "Startup"
        / SHORTCUT_NAME
    )


def sync_startup_shortcut(paths: AppPaths, config: AppConfig) -> None:
    shortcut_path = startup_shortcut_path()
    if config.start_tray_on_login and config.first_run_completed:
        shortcut_path.parent.mkdir(parents=True, exist_ok=True)
        _create_shortcut(shortcut_path, _resolve_tray_shortcut_spec(paths))
        return
    if shortcut_path.exists():
        shortcut_path.unlink()


def _resolve_tray_shortcut_spec(paths: AppPaths) -> ShortcutSpec:
    invocation = resolve_tray_background_invocation(paths)
    return ShortcutSpec(
        target=invocation.executable,
        arguments=invocation.argument_string(),
        working_directory=invocation.working_directory,
    )


def remove_startup_shortcut() -> None:
    shortcut_path = startup_shortcut_path()
    if shortcut_path.exists():
        shortcut_path.unlink()


def _create_shortcut(shortcut_path: Path, spec: ShortcutSpec) -> None:
    try:
        import win32com.client  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - Windows-only optional integration
        raise RuntimeError("pywin32 is required to manage the startup shortcut") from exc

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.TargetPath = spec.target
    shortcut.Arguments = spec.arguments
    shortcut.WorkingDirectory = spec.working_directory
    shortcut.Save()
