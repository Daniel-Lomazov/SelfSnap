from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys

from selfsnap.models import AppConfig
from selfsnap.paths import AppPaths


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
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / SHORTCUT_NAME


def sync_startup_shortcut(paths: AppPaths, config: AppConfig) -> None:
    shortcut_path = startup_shortcut_path()
    if config.start_tray_on_login:
        shortcut_path.parent.mkdir(parents=True, exist_ok=True)
        _create_shortcut(shortcut_path, _resolve_tray_shortcut_spec(paths))
        return
    if shortcut_path.exists():
        shortcut_path.unlink()


def _resolve_tray_shortcut_spec(paths: AppPaths) -> ShortcutSpec:
    wrapper_path = paths.bin_dir / "SelfSnap.cmd"
    if wrapper_path.exists():
        return ShortcutSpec(
            target=str(wrapper_path),
            arguments="tray",
            working_directory=str(paths.bin_dir),
        )
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable)
        return ShortcutSpec(
            target=str(executable),
            arguments="",
            working_directory=str(executable.parent),
        )
    python_executable = sys.executable
    if not python_executable:
        raise RuntimeError("Python executable path is unavailable for startup shortcut creation")
    return ShortcutSpec(
        target=python_executable,
        arguments="-m selfsnap tray",
        working_directory=str(paths.root),
    )


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
