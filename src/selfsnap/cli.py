from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from selfsnap.config_store import load_or_create_config
from selfsnap.db import connect, ensure_database
from selfsnap.lifecycle_actions import (
    resolve_reinstall_invocation,
    resolve_uninstall_invocation,
    run_lifecycle_script_and_check,
)
from selfsnap.logging_setup import setup_logging
from selfsnap.models import TriggerSource
from selfsnap.paths import resolve_app_paths
from selfsnap.records import get_latest_record
from selfsnap.runtime_probe import probe_runtime_dependencies
from selfsnap.update_checker import compare_versions, fetch_latest_release_tag
from selfsnap.version import __version__
from selfsnap.worker import run_capture_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="selfsnap")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tray_parser = subparsers.add_parser("tray", help="Run the tray application")
    tray_parser.set_defaults(handler=handle_tray)

    capture_parser = subparsers.add_parser("capture", help="Run a manual or scheduled capture")
    capture_parser.add_argument(
        "--trigger", choices=[item.value for item in TriggerSource], required=True
    )
    capture_parser.add_argument("--schedule-id")
    capture_parser.add_argument("--planned-local-ts")
    capture_parser.set_defaults(handler=handle_capture)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="Record missed recurring schedule occurrences"
    )
    reconcile_parser.set_defaults(handler=handle_reconcile)

    sync_parser = subparsers.add_parser(
        "sync-scheduler", help="Sync Task Scheduler tasks from config"
    )
    sync_parser.set_defaults(handler=handle_sync_scheduler)

    reinstall_parser = subparsers.add_parser(
        "reinstall", help="Reinstall SelfSnap in-place from the current source checkout"
    )
    reinstall_parser.add_argument(
        "--relaunch-tray",
        action="store_true",
        default=False,
        help="Relaunch the tray after reinstall completes",
    )
    reinstall_parser.set_defaults(handler=handle_reinstall)

    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall SelfSnap")
    uninstall_parser.add_argument(
        "--remove-user-data",
        action="store_true",
        default=False,
        help="Also remove all user data (config, database, captures, logs)",
    )
    uninstall_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        default=False,
        help="Skip confirmation prompt",
    )
    uninstall_parser.set_defaults(handler=handle_uninstall)

    update_parser = subparsers.add_parser(
        "update", help="Check for a new release and update if one is available"
    )
    update_parser.add_argument(
        "--check-only",
        action="store_true",
        default=False,
        help="Only report whether an update is available; do not install",
    )
    update_parser.add_argument(
        "--relaunch-tray",
        action="store_true",
        default=False,
        help="Relaunch the tray after the update completes",
    )
    update_parser.set_defaults(handler=handle_update)

    diag_parser = subparsers.add_parser("diag", help="Print runtime diagnostics")
    diag_parser.set_defaults(handler=handle_diag)

    doctor_parser = subparsers.add_parser("doctor", help="Validate runtime dependencies")
    doctor_parser.set_defaults(handler=handle_doctor)
    return parser


def handle_capture(args: argparse.Namespace) -> int:
    paths = resolve_app_paths()
    config = load_or_create_config(paths)
    setup_logging(paths, config.log_level)
    result = run_capture_command(
        trigger_source=TriggerSource(args.trigger),
        schedule_id=args.schedule_id,
        planned_local_ts=args.planned_local_ts,
        paths=paths,
    )
    print(result.message)
    return result.exit_code


def handle_tray(_args: argparse.Namespace) -> int:
    from selfsnap.tray.app import run_tray_app

    return run_tray_app()


def handle_reconcile(_args: argparse.Namespace) -> int:
    from selfsnap.scheduler.reconcile import reconcile_missed_slots

    return reconcile_missed_slots(emit_console=True)


def handle_sync_scheduler(_args: argparse.Namespace) -> int:
    from selfsnap.scheduler.task_scheduler import sync_scheduler_from_config

    return sync_scheduler_from_config()


def handle_reinstall(args: argparse.Namespace) -> int:
    paths = resolve_app_paths()
    print("Reinstalling SelfSnap…")
    spec = resolve_reinstall_invocation(
        paths, update_source=False, relaunch_tray=args.relaunch_tray
    )
    if run_lifecycle_script_and_check(spec):
        print("Reinstall completed successfully.")
        return 0
    print("Reinstall failed. Check the reinstall.ps1 output for details.", file=sys.stderr)
    return 1


def handle_uninstall(args: argparse.Namespace) -> int:
    if not args.yes:
        prompt = (
            "Remove all SelfSnap user data? [y/N] "
            if args.remove_user_data
            else "Uninstall SelfSnap? [y/N] "
        )
        answer = input(prompt).strip().lower()
        if answer not in ("y", "yes"):
            print("Uninstall cancelled.")
            return 0

    paths = resolve_app_paths()
    print("Uninstalling SelfSnap…")
    spec = resolve_uninstall_invocation(paths, remove_user_data=args.remove_user_data)
    if run_lifecycle_script_and_check(spec):
        print("Uninstall completed successfully.")
        return 0
    print("Uninstall failed. Check the uninstall.ps1 output for details.", file=sys.stderr)
    return 1


def handle_update(args: argparse.Namespace) -> int:
    print("Checking for updates…")
    latest_tag = fetch_latest_release_tag("Daniel-Lomazov/SelfSnap")
    if latest_tag is None:
        print(
            "Could not reach GitHub. Verify your internet connection and try again.",
            file=sys.stderr,
        )
        return 1

    comparison = compare_versions(__version__, latest_tag)
    if comparison >= 0:
        effective_latest = f"v{__version__}" if comparison > 0 else latest_tag
        print(f"Already up to date. Installed: v{__version__}  Latest: {effective_latest}")
        return 0

    print(f"Update available: v{__version__} → {latest_tag}")
    if args.check_only:
        return 0

    print(f"Installing {latest_tag}…")
    paths = resolve_app_paths()
    spec = resolve_reinstall_invocation(
        paths, update_source=True, target_tag=latest_tag, relaunch_tray=args.relaunch_tray
    )
    if run_lifecycle_script_and_check(spec):
        print(f"Updated to {latest_tag} successfully.")
        return 0
    print(
        f"Update to {latest_tag} failed. Check that you have network access and the tag exists.",
        file=sys.stderr,
    )
    return 1


def handle_diag(_args: argparse.Namespace) -> int:
    paths = resolve_app_paths()
    config = load_or_create_config(paths)
    ensure_database(paths.db_path)
    setup_logging(paths, config.log_level)
    from selfsnap.scheduler.task_scheduler import read_registered_task_details

    with connect(paths.db_path) as connection:
        latest = get_latest_record(connection)
    payload = {
        "version": __version__,
        "paths": {
            "root": str(paths.root),
            "config_path": str(paths.config_path),
            "db_path": str(paths.db_path),
            "log_path": str(paths.log_path),
            "default_capture_root": str(paths.default_capture_root),
            "default_archive_root": str(paths.default_archive_root),
            "onedrive_capture_root": str(paths.onedrive_capture_root()),
            "onedrive_archive_root": str(paths.onedrive_archive_root()),
            "bin_dir": str(paths.bin_dir),
        },
        "config": config.to_dict(),
        "resolved_storage": {
            "storage_preset": config.storage_preset,
            "capture_root": str(paths.resolve_capture_root(config)),
            "archive_root": str(paths.resolve_archive_root(config)),
        },
        "latest_record": asdict(latest) if latest else None,
        "scheduled_tasks": read_registered_task_details(),
        "runtime_probe": probe_runtime_dependencies().to_dict(),
        "python": sys.version,
        "cwd": str(Path.cwd()),
    }
    print(json.dumps(payload, indent=2))
    return 0


def handle_doctor(_args: argparse.Namespace) -> int:
    probe = probe_runtime_dependencies()
    print(json.dumps(probe.to_dict(), indent=2))
    return 0 if probe.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))
