from __future__ import annotations

import json
from pathlib import Path


def test_readme_describes_recurring_schedule_setup() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Current version: `0.8.0`" in readme
    assert "docs/releases/v0.8.0.md" in readme
    assert "CHANGELOG.md" in readme
    assert "Existing daily schedules are migrated into the new recurrence model automatically." in readme
    assert "Fast schedules such as `seconds` and `minutes` are tray-managed" in readme
    assert "Windows Task Scheduler." in readme
    assert "same-second file collisions" in readme
    assert "How to add scheduled captures" in readme
    assert "Every N seconds/minutes/hours/days/weeks/months/years" in readme
    assert "Every 1 day" in readme
    assert "start date = today" in readme
    assert "start time = now" in readme
    assert "You can type the date and time by hand" in readme
    assert "Multi-select is for deleting several schedules at once." in readme
    assert "months" in readme and "years" in readme
    assert "High-frequency schedules" in readme
    assert "Task Scheduler-backed" in readme


def test_sample_config_uses_recurring_schedule_schema() -> None:
    config = json.loads(Path("sample/config.example.json").read_text(encoding="utf-8"))

    assert config["schema_version"] == 2
    assert config["schedules"][0]["interval_value"] == 1
    assert config["schedules"][0]["interval_unit"] == "day"
    assert config["schedules"][0]["start_date_local"] == "2026-03-23"
    assert config["schedules"][0]["start_time_local"] == "09:00:00"
    assert config["schedules"][1]["interval_unit"] == "minute"
    assert "local_time" not in config["schedules"][0]


def test_version_files_are_aligned_to_0_8_0() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    version_file = Path("src/selfsnap/version.py").read_text(encoding="utf-8")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    assert 'version = "0.8.0"' in pyproject
    assert '__version__ = "0.8.0"' in version_file
    assert "## v0.8.0 - 2026-03-23" in changelog
    assert "recurrence schema" in changelog.lower()
    assert "hybrid runtime model" in changelog.lower()
    assert "migrated into the new recurrence model" in changelog.lower() or "automatic migration of legacy daily schedules" in changelog.lower()
    assert "structured editor" in changelog.lower()


def test_product_release_notes_exist_for_v0_8_0() -> None:
    release_notes = Path("docs/releases/v0.8.0.md").read_text(encoding="utf-8")

    assert "Every N seconds" in release_notes
    assert "minutes" in release_notes
    assert "hours" in release_notes
    assert "days" in release_notes
    assert "weeks" in release_notes
    assert "months" in release_notes
    assert "years" in release_notes
    assert "Every 1 day" in release_notes
    assert "start date = today" in release_notes
    assert "start time = now" in release_notes
    assert "tray while the tray is running" in release_notes
    assert "Windows Task Scheduler" in release_notes
    assert "skip invalid dates" in release_notes


def test_release_workflow_prefers_release_notes_doc() -> None:
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "docs/releases/${tag}.md" in workflow
    assert "fs.existsSync(releaseNotesPath)" in workflow
    assert 'fs.readFileSync(releaseNotesPath, "utf8")' in workflow
    assert 'changelog.slice(start' in workflow
