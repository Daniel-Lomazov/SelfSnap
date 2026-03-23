from __future__ import annotations
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

from selfsnap.config_store import save_config
from selfsnap.db import connect, ensure_database
from selfsnap.issue_reporting import (
    DEFAULT_GITHUB_REPO,
    build_issue_body,
    build_issue_title,
    build_issue_url,
    collect_safe_issue_diagnostics,
    submit_issue_report,
)
from selfsnap.models import AppConfig, CaptureRecord
from selfsnap.records import insert_capture_record
from selfsnap.version import __version__


def _sample_record(image_path: str) -> CaptureRecord:
    now = datetime.now(UTC).isoformat()
    return CaptureRecord(
        record_id="record-1",
        trigger_source="manual",
        schedule_id=None,
        planned_local_ts=None,
        started_utc=now,
        finished_utc=now,
        outcome_category="success",
        outcome_code="capture_saved",
        image_path=image_path,
        file_present=True,
        image_sha256="abc123",
        monitor_count=1,
        composite_width=100,
        composite_height=50,
        file_bytes=2048,
        error_code=None,
        error_message=None,
        archived=False,
        archived_at_utc=None,
        retention_deleted_at_utc=None,
        app_version="0.1.0",
        created_utc=now,
    )


def test_build_issue_title_uses_short_summary() -> None:
    title = build_issue_title("Settings window reopened smaller after manual capture.")

    assert title == "App report: Settings window reopened smaller after manual capture"


def test_build_issue_body_includes_safe_diagnostics_without_local_paths(temp_paths) -> None:
    config = AppConfig(
        storage_preset="custom",
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
    )
    save_config(temp_paths, config)
    ensure_database(temp_paths.db_path)
    with connect(temp_paths.db_path) as connection:
        insert_capture_record(
            connection, _sample_record(str(temp_paths.default_capture_root / "cap.png"))
        )

    body = build_issue_body(
        temp_paths, "Manual capture reopened Settings smaller.", include_diagnostics=True
    )

    assert "<!-- reported-via-selfsnap -->" in body
    assert "## User report" in body
    assert "Storage preset: custom" in body
    assert "Latest outcome: success/capture_saved" in body
    assert str(temp_paths.default_capture_root) not in body
    assert "cap.png" not in body


def test_collect_safe_issue_diagnostics_reports_runtime_context(temp_paths) -> None:
    diagnostics = collect_safe_issue_diagnostics(temp_paths)

    assert diagnostics["App version"] == __version__
    assert diagnostics["Storage preset"] == "local_pictures"
    assert diagnostics["Schedule count"] == "0"


def test_build_issue_url_targets_default_report_template() -> None:
    url = build_issue_url(DEFAULT_GITHUB_REPO, "App report: Example", "## User report\nExample")
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.netloc == "github.com"
    assert parsed.path == f"/{DEFAULT_GITHUB_REPO}/issues/new"
    assert query["template"] == ["report_issue.md"]
    assert query["title"] == ["App report: Example"]


def test_submit_issue_report_opens_browser(temp_paths, monkeypatch) -> None:
    opened: list[str] = []
    monkeypatch.setattr(
        "selfsnap.issue_reporting.webbrowser.open", lambda url: opened.append(url) or True
    )

    result = submit_issue_report(
        temp_paths, "The tray did not open the report dialog.", include_diagnostics=False
    )

    assert result.ok is True
    assert result.method == "browser"
    assert len(opened) == 1
    assert "issues/new" in opened[0]


def test_submit_issue_report_ignores_token_environment_variables(temp_paths, monkeypatch) -> None:
    opened: list[str] = []
    monkeypatch.setenv("SELFSNAP_GITHUB_TOKEN", "token")
    monkeypatch.setenv("GH_TOKEN", "token")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setattr(
        "selfsnap.issue_reporting.webbrowser.open", lambda url: opened.append(url) or True
    )

    result = submit_issue_report(
        temp_paths, "The tray did not open the report dialog.", include_diagnostics=False
    )

    assert result.ok is True
    assert result.method == "browser"
    assert len(opened) == 1
