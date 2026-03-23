from __future__ import annotations

import json
import os
import platform
import sys
import webbrowser
from dataclasses import dataclass
from typing import Any
from urllib import error as urllib_error
from urllib import parse, request

from selfsnap.config_store import load_or_create_config
from selfsnap.db import connect, ensure_database
from selfsnap.paths import AppPaths
from selfsnap.records import get_latest_record
from selfsnap.runtime_launch import read_install_metadata
from selfsnap.runtime_probe import probe_runtime_dependencies
from selfsnap.version import __version__

DEFAULT_GITHUB_REPO = "Daniel-Lomazov/SelfSnap"
DEFAULT_ISSUE_TEMPLATE = "report_issue.md"
ISSUE_MARKER = "<!-- reported-via-selfsnap -->"


@dataclass(slots=True)
class IssueSubmissionResult:
    ok: bool
    method: str
    issue_url: str
    message: str


def submit_issue_report(
    paths: AppPaths,
    description: str,
    *,
    include_diagnostics: bool = True,
) -> IssueSubmissionResult:
    title = build_issue_title(description)
    body = build_issue_body(paths, description, include_diagnostics=include_diagnostics)
    repo = resolve_issue_repo()
    token = resolve_issue_token()
    if token:
        result = _submit_issue_via_api(repo, title, body, token)
        if result.ok:
            return result
    return _open_issue_in_browser(repo, title, body)


def build_issue_title(description: str) -> str:
    cleaned = " ".join(description.strip().split())
    if not cleaned:
        raise ValueError("Issue description must not be empty.")
    sentence = cleaned.split(".", maxsplit=1)[0].strip() or cleaned
    if len(sentence) > 72:
        sentence = sentence[:69].rstrip() + "..."
    return f"App report: {sentence}"


def build_issue_body(paths: AppPaths, description: str, *, include_diagnostics: bool = True) -> str:
    user_text = description.strip()
    if not user_text:
        raise ValueError("Issue description must not be empty.")
    diagnostics = collect_safe_issue_diagnostics(paths) if include_diagnostics else None
    lines = [
        ISSUE_MARKER,
        "submitted_from=selfsnap",
        "issue_kind=bug",
        "area=other",
        "impact=unknown",
        f"app_version={__version__}",
        f"diag_included={'yes' if include_diagnostics else 'no'}",
        "",
        "## User report",
        user_text,
        "",
        "## Expected behavior",
        "_Please describe what you expected to happen instead._",
        "",
        "## Reproduction notes",
        "_Optional: mention the last action you took before the problem._",
    ]
    if diagnostics:
        lines.extend(["", "## Safe diagnostics"])
        for key, value in diagnostics.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.extend(
            [
                "",
                "## Safe diagnostics",
                (
                    "_Diagnostics were not included from the app. Paste `selfsnap diag` "
                    "or `selfsnap doctor` only if you want to share them._"
                ),
            ]
        )
    return "\n".join(lines).strip() + "\n"


def build_issue_url(
    repo: str, title: str, body: str, *, template: str = DEFAULT_ISSUE_TEMPLATE
) -> str:
    query = parse.urlencode(
        {"template": template, "title": title, "body": body}, quote_via=parse.quote
    )
    return f"https://github.com/{repo}/issues/new?{query}"


def collect_safe_issue_diagnostics(paths: AppPaths) -> dict[str, str]:
    config = load_or_create_config(paths)
    latest_record = None
    if paths.db_path.exists():
        ensure_database(paths.db_path)
        with connect(paths.db_path) as connection:
            latest_record = get_latest_record(connection)
    runtime_probe = probe_runtime_dependencies()
    install_metadata = read_install_metadata(paths)
    install_mode = "installed-wrapper" if install_metadata else "source"
    if getattr(sys, "frozen", False):
        install_mode = "packaged"
    diagnostics: dict[str, str] = {
        "App version": __version__,
        "Install mode": install_mode,
        "Python": platform.python_version(),
        "Windows": platform.platform(),
        "Storage preset": config.storage_preset,
        "Scheduler sync state": config.scheduler_sync_state,
        "Schedule count": str(len(config.schedules)),
        "Start tray on login": _yes_no(config.start_tray_on_login),
        "Wake for scheduled captures": _yes_no(config.wake_for_scheduled_captures),
        "Runtime probe": runtime_probe.summary,
    }
    if latest_record is None:
        diagnostics["Latest outcome"] = "none"
    else:
        diagnostics["Latest outcome"] = (
            f"{latest_record.outcome_category}/{latest_record.outcome_code}"
        )
        diagnostics["Latest trigger"] = latest_record.trigger_source
        diagnostics["Latest created UTC"] = latest_record.created_utc
    return diagnostics


def resolve_issue_repo() -> str:
    return os.environ.get("SELFSNAP_GITHUB_REPO", DEFAULT_GITHUB_REPO)


def resolve_issue_token() -> str | None:
    for env_name in ("SELFSNAP_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(env_name)
        if value:
            return value
    return None


def _submit_issue_via_api(repo: str, title: str, body: str, token: str) -> IssueSubmissionResult:
    payload = json.dumps({"title": title, "body": body}).encode("utf-8")
    api_url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": f"selfsnap-win11/{__version__}",
    }
    try:
        api_request = request.Request(api_url, data=payload, headers=headers, method="POST")
        with request.urlopen(api_request, timeout=10) as response:
            issue_payload: dict[str, Any] = json.load(response)
    except (
        TimeoutError,
        OSError,
        urllib_error.HTTPError,
        urllib_error.URLError,
        json.JSONDecodeError,
    ):
        return IssueSubmissionResult(
            ok=False,
            method="api",
            issue_url="",
            message="Direct GitHub issue submission failed; falling back to the browser flow.",
        )
    issue_url = str(issue_payload.get("html_url", ""))
    return IssueSubmissionResult(
        ok=True,
        method="api",
        issue_url=issue_url,
        message=f"Issue created on GitHub: {issue_url}",
    )


def _open_issue_in_browser(repo: str, title: str, body: str) -> IssueSubmissionResult:
    issue_url = build_issue_url(repo, title, body)
    opened = False
    try:
        opened = bool(webbrowser.open(issue_url))
    except Exception:
        opened = False
    if not opened and os.name == "nt":
        try:
            os.startfile(issue_url)
            opened = True
        except OSError:
            opened = False
    if not opened:
        return IssueSubmissionResult(
            ok=False,
            method="browser",
            issue_url=issue_url,
            message="Could not open a browser for GitHub issue reporting.",
        )
    return IssueSubmissionResult(
        ok=True,
        method="browser",
        issue_url=issue_url,
        message=(
            "A prefilled GitHub issue page was opened in your browser. "
            "Review it and submit it there."
        ),
    )


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
