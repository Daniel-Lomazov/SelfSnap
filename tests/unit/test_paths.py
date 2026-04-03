"""Tests for selfsnap.paths — path resolution, fallbacks, and collision handling."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from selfsnap.models import TriggerSource
from selfsnap.paths import AppPaths, resolve_app_paths

# ---------------------------------------------------------------------------
# resolve_app_paths — env var fallbacks
# ---------------------------------------------------------------------------


def test_resolve_app_paths_uses_localappdata_env(tmp_path, monkeypatch) -> None:
    local_appdata = tmp_path / "AppData" / "Local"
    local_appdata.mkdir(parents=True)
    monkeypatch.setenv("LOCALAPPDATA", str(local_appdata))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    paths = resolve_app_paths()

    assert paths.root == local_appdata / "SelfSnap"
    assert paths.user_profile == tmp_path


def test_resolve_app_paths_falls_back_when_localappdata_unset(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    paths = resolve_app_paths()

    # Falls back to home-based path — just assert it produces an AppPaths
    assert isinstance(paths, AppPaths)
    assert "SelfSnap" in str(paths.root)


def test_resolve_app_paths_falls_back_when_userprofile_unset(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))
    monkeypatch.delenv("USERPROFILE", raising=False)

    paths = resolve_app_paths()

    assert isinstance(paths, AppPaths)


# ---------------------------------------------------------------------------
# capture_file_path — naming convention
# ---------------------------------------------------------------------------


def test_capture_file_path_uses_schedule_id_as_suffix(temp_paths) -> None:
    when = datetime(2026, 4, 3, 14, 30, 0)
    path = temp_paths.capture_file_path(
        temp_paths.default_capture_root, when, TriggerSource.SCHEDULED, "morning"
    )
    assert "morning" in path.name
    assert path.suffix == ".png"
    assert "2026" in str(path)


def test_capture_file_path_uses_manual_suffix_when_no_schedule(temp_paths) -> None:
    when = datetime(2026, 4, 3, 14, 30, 0)
    path = temp_paths.capture_file_path(
        temp_paths.default_capture_root, when, TriggerSource.MANUAL, None
    )
    assert "manual" in path.name


# ---------------------------------------------------------------------------
# archive_file_path — collision handling
# ---------------------------------------------------------------------------


def test_archive_file_path_returns_destination_when_no_collision(temp_paths) -> None:
    capture_root = temp_paths.default_capture_root
    source = capture_root / "2026" / "04" / "03" / "cap.png"
    archive_root = temp_paths.default_archive_root
    now = datetime(2026, 4, 3, 14, 0, 0).astimezone()

    result = temp_paths.archive_file_path(archive_root, capture_root, source, now)

    # No collision — returns the canonical archive path
    assert result == archive_root / "2026" / "04" / "03" / "cap.png"


def test_archive_file_path_adds_timestamp_suffix_on_collision(temp_paths) -> None:
    capture_root = temp_paths.default_capture_root
    source = capture_root / "2026" / "04" / "03" / "cap.png"
    archive_root = temp_paths.default_archive_root

    # Pre-create the destination so a collision exists
    dest = archive_root / "2026" / "04" / "03" / "cap.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"existing")

    now = datetime(2026, 4, 3, 14, 0, 0).astimezone()
    result = temp_paths.archive_file_path(archive_root, capture_root, source, now)

    # Collision detected — name should contain the timestamp portion
    assert result.name != "cap.png"
    assert "cap_" in result.name
    assert result.suffix == ".png"


def test_archive_file_path_handles_source_outside_capture_root(temp_paths) -> None:
    """When relative_to fails, falls back to just the filename."""
    capture_root = temp_paths.default_capture_root
    source = Path("C:\\some\\other\\location\\cap.png")
    archive_root = temp_paths.default_archive_root
    now = datetime(2026, 4, 3, 14, 0, 0).astimezone()

    result = temp_paths.archive_file_path(archive_root, capture_root, source, now)

    # Falls back to filename only — result should have the same name
    assert result.name == "cap.png" or "cap" in result.name


# ---------------------------------------------------------------------------
# AppPaths.preferred_onedrive_root — env var override
# ---------------------------------------------------------------------------


def test_preferred_onedrive_root_uses_env_var(temp_paths, monkeypatch) -> None:
    custom = temp_paths.user_profile / "MyOneDrive"
    monkeypatch.setenv("OneDrive", str(custom))
    result = temp_paths.preferred_onedrive_root()
    assert result == custom


def test_preferred_onedrive_root_falls_back_without_env(temp_paths, monkeypatch) -> None:
    monkeypatch.delenv("OneDrive", raising=False)
    result = temp_paths.preferred_onedrive_root()
    assert result == temp_paths.user_profile / "OneDrive"
