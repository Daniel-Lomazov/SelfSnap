from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from selfsnap.config_store import load_or_create_config
from selfsnap.db import connect, ensure_database
from selfsnap.logging_setup import setup_logging
from selfsnap.models import TriggerSource
from selfsnap.paths import resolve_app_paths
from selfsnap.records import get_latest_record
from selfsnap.version import __version__
from selfsnap.worker import run_capture_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="selfsnap")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tray_parser = subparsers.add_parser("tray", help="Run the tray application")
    tray_parser.set_defaults(handler=handle_tray)

    capture_parser = subparsers.add_parser("capture", help="Run a manual or scheduled capture")
    capture_parser.add_argument("--trigger", choices=[item.value for item in TriggerSource], required=True)
    capture_parser.add_argument("--schedule-id")
    capture_parser.add_argument("--planned-local-ts")
    capture_parser.set_defaults(handler=handle_capture)

    reconcile_parser = subparsers.add_parser("reconcile", help="Record missed schedule slots")
    reconcile_parser.set_defaults(handler=handle_reconcile)

    sync_parser = subparsers.add_parser("sync-scheduler", help="Sync Task Scheduler tasks from config")
    sync_parser.set_defaults(handler=handle_sync_scheduler)

    diag_parser = subparsers.add_parser("diag", help="Print runtime diagnostics")
    diag_parser.set_defaults(handler=handle_diag)
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

    return reconcile_missed_slots()


def handle_sync_scheduler(_args: argparse.Namespace) -> int:
    from selfsnap.scheduler.task_scheduler import sync_scheduler_from_config

    return sync_scheduler_from_config()


def handle_diag(_args: argparse.Namespace) -> int:
    paths = resolve_app_paths()
    config = load_or_create_config(paths)
    ensure_database(paths.db_path)
    setup_logging(paths, config.log_level)
    with connect(paths.db_path) as connection:
        latest = get_latest_record(connection)
    payload = {
        "version": __version__,
        "paths": {
            "root": str(paths.root),
            "config_path": str(paths.config_path),
            "db_path": str(paths.db_path),
            "log_path": str(paths.log_path),
        },
        "config": config.to_dict(),
        "latest_record": asdict(latest) if latest else None,
        "python": sys.version,
        "cwd": str(Path.cwd()),
    }
    print(json.dumps(payload, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))
