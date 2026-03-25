from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from selfsnap.cli import build_parser, handle_reinstall, handle_uninstall, handle_update


# ---------------------------------------------------------------------------
# parser shape
# ---------------------------------------------------------------------------


def test_parser_has_reinstall_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(["reinstall"])
    assert args.command == "reinstall"
    assert args.relaunch_tray is False
    assert args.handler is handle_reinstall


def test_parser_reinstall_relaunch_tray_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["reinstall", "--relaunch-tray"])
    assert args.relaunch_tray is True


def test_parser_has_uninstall_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(["uninstall"])
    assert args.command == "uninstall"
    assert args.remove_user_data is False
    assert args.yes is False
    assert args.handler is handle_uninstall


def test_parser_uninstall_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["uninstall", "--remove-user-data", "--yes"])
    assert args.remove_user_data is True
    assert args.yes is True


def test_parser_has_update_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(["update"])
    assert args.command == "update"
    assert args.check_only is False
    assert args.relaunch_tray is False
    assert args.handler is handle_update


def test_parser_update_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["update", "--check-only", "--relaunch-tray"])
    assert args.check_only is True
    assert args.relaunch_tray is True


# ---------------------------------------------------------------------------
# handle_reinstall
# ---------------------------------------------------------------------------


def _reinstall_args(relaunch_tray: bool = False):
    parser = build_parser()
    return parser.parse_args(["reinstall"] + (["--relaunch-tray"] if relaunch_tray else []))


def test_handle_reinstall_returns_0_on_success(temp_paths, monkeypatch) -> None:
    monkeypatch.setattr("selfsnap.cli.resolve_app_paths", lambda: temp_paths)
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_source_repo_root",
        lambda _p: str(temp_paths.user_profile),
    )
    scripts_dir = temp_paths.user_profile / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "reinstall.ps1").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_foreground_python_executable",
        lambda _p: r"C:\Python312\python.exe",
    )
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_background_python_executable",
        lambda _p: r"C:\Python312\pythonw.exe",
    )
    monkeypatch.setattr(
        "selfsnap.cli.run_lifecycle_script_and_check",
        lambda _spec: True,
    )
    assert handle_reinstall(_reinstall_args()) == 0


def test_handle_reinstall_returns_1_on_failure(temp_paths, monkeypatch) -> None:
    monkeypatch.setattr("selfsnap.cli.resolve_app_paths", lambda: temp_paths)
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_source_repo_root",
        lambda _p: str(temp_paths.user_profile),
    )
    scripts_dir = temp_paths.user_profile / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "reinstall.ps1").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_foreground_python_executable",
        lambda _p: r"C:\Python312\python.exe",
    )
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_background_python_executable",
        lambda _p: r"C:\Python312\pythonw.exe",
    )
    monkeypatch.setattr(
        "selfsnap.cli.run_lifecycle_script_and_check",
        lambda _spec: False,
    )
    assert handle_reinstall(_reinstall_args()) == 1


# ---------------------------------------------------------------------------
# handle_uninstall
# ---------------------------------------------------------------------------


def _uninstall_args(remove_user_data: bool = False, yes: bool = True):
    parts = ["uninstall"]
    if remove_user_data:
        parts.append("--remove-user-data")
    if yes:
        parts.append("--yes")
    return build_parser().parse_args(parts)


def test_handle_uninstall_returns_0_on_success(temp_paths, monkeypatch) -> None:
    monkeypatch.setattr("selfsnap.cli.resolve_app_paths", lambda: temp_paths)
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_source_repo_root",
        lambda _p: str(temp_paths.user_profile),
    )
    scripts_dir = temp_paths.user_profile / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "uninstall.ps1").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_foreground_python_executable",
        lambda _p: r"C:\Python312\python.exe",
    )
    monkeypatch.setattr(
        "selfsnap.cli.run_lifecycle_script_and_check",
        lambda _spec: True,
    )
    assert handle_uninstall(_uninstall_args(yes=True)) == 0


def test_handle_uninstall_cancelled_without_yes_flag(temp_paths, monkeypatch, capsys) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert handle_uninstall(_uninstall_args(yes=False)) == 0
    out = capsys.readouterr().out
    assert "cancelled" in out.lower()


def test_handle_uninstall_proceeds_on_yes_input(temp_paths, monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    monkeypatch.setattr("selfsnap.cli.resolve_app_paths", lambda: temp_paths)
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_source_repo_root",
        lambda _p: str(temp_paths.user_profile),
    )
    scripts_dir = temp_paths.user_profile / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "uninstall.ps1").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_foreground_python_executable",
        lambda _p: r"C:\Python312\python.exe",
    )
    monkeypatch.setattr(
        "selfsnap.cli.run_lifecycle_script_and_check",
        lambda _spec: True,
    )
    assert handle_uninstall(_uninstall_args(yes=False)) == 0


# ---------------------------------------------------------------------------
# handle_update
# ---------------------------------------------------------------------------


def _update_args(check_only: bool = False, relaunch_tray: bool = False):
    parts = ["update"]
    if check_only:
        parts.append("--check-only")
    if relaunch_tray:
        parts.append("--relaunch-tray")
    return build_parser().parse_args(parts)


def test_handle_update_already_up_to_date(monkeypatch, capsys) -> None:
    from selfsnap import version as _ver

    monkeypatch.setattr(
        "selfsnap.cli.fetch_latest_release_tag",
        lambda _repo: f"v{_ver.__version__}",
    )
    assert handle_update(_update_args()) == 0
    assert "up to date" in capsys.readouterr().out.lower()


def test_handle_update_network_error_returns_1(monkeypatch) -> None:
    monkeypatch.setattr("selfsnap.cli.fetch_latest_release_tag", lambda _repo: None)
    assert handle_update(_update_args()) == 1


def test_handle_update_check_only_reports_available_without_installing(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(
        "selfsnap.cli.fetch_latest_release_tag", lambda _repo: "v99.0.0"
    )
    ran_install = []
    monkeypatch.setattr(
        "selfsnap.cli.run_lifecycle_script_and_check",
        lambda _spec: ran_install.append(1) or True,
    )
    result = handle_update(_update_args(check_only=True))
    assert result == 0
    assert not ran_install
    assert "99.0.0" in capsys.readouterr().out


def test_handle_update_installs_when_newer_available(temp_paths, monkeypatch) -> None:
    monkeypatch.setattr(
        "selfsnap.cli.fetch_latest_release_tag", lambda _repo: "v99.0.0"
    )
    monkeypatch.setattr("selfsnap.cli.resolve_app_paths", lambda: temp_paths)
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_source_repo_root",
        lambda _p: str(temp_paths.user_profile),
    )
    scripts_dir = temp_paths.user_profile / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "reinstall.ps1").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_foreground_python_executable",
        lambda _p: r"C:\Python312\python.exe",
    )
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_background_python_executable",
        lambda _p: r"C:\Python312\pythonw.exe",
    )
    monkeypatch.setattr(
        "selfsnap.cli.run_lifecycle_script_and_check", lambda _spec: True
    )
    assert handle_update(_update_args()) == 0


def test_handle_update_returns_1_on_install_failure(temp_paths, monkeypatch) -> None:
    monkeypatch.setattr(
        "selfsnap.cli.fetch_latest_release_tag", lambda _repo: "v99.0.0"
    )
    monkeypatch.setattr("selfsnap.cli.resolve_app_paths", lambda: temp_paths)
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_source_repo_root",
        lambda _p: str(temp_paths.user_profile),
    )
    scripts_dir = temp_paths.user_profile / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "reinstall.ps1").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_foreground_python_executable",
        lambda _p: r"C:\Python312\python.exe",
    )
    monkeypatch.setattr(
        "selfsnap.lifecycle_actions.resolve_background_python_executable",
        lambda _p: r"C:\Python312\pythonw.exe",
    )
    monkeypatch.setattr(
        "selfsnap.cli.run_lifecycle_script_and_check", lambda _spec: False
    )
    assert handle_update(_update_args()) == 1
