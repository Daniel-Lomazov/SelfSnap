from __future__ import annotations

import json
from pathlib import Path


def test_readme_describes_recurring_schedule_setup() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Current version: `0.8.0`" in readme
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
    assert "recurring schedule" in changelog.lower()
