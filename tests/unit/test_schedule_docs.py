from __future__ import annotations

import json
from pathlib import Path
import re


def _read_project_version() -> str:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    assert match is not None
    return match.group(1)


def test_readme_describes_recurring_schedule_setup() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    version = _read_project_version()

    assert f"Current version: `v{version}`" in readme
    assert "CHANGELOG.md" in readme
    assert "RELEASE_CRITERIA_1_0.md" in readme
    assert "High-frequency schedules such as `seconds` and `minutes` are tray-managed" in readme
    assert "Windows Task Scheduler" in readme
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


def test_product_config_example_uses_recurring_schedule_schema() -> None:
    config = json.loads(Path("docs/product/config.example.json").read_text(encoding="utf-8"))

    assert config["schema_version"] == 3
    assert config["schedules"][0]["interval_value"] == 1
    assert config["schedules"][0]["interval_unit"] == "day"
    assert config["schedules"][0]["start_date_local"] == "2026-03-23"
    assert config["schedules"][0]["start_time_local"] == "09:00:00"
    assert config["schedules"][1]["interval_unit"] == "minute"
    assert "local_time" not in config["schedules"][0]


def test_version_files_are_aligned() -> None:
    version = _read_project_version()
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    version_file = Path("src/selfsnap/version.py").read_text(encoding="utf-8")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    assert f'version = "{version}"' in pyproject
    assert f'__version__ = "{version}"' in version_file
    assert f"## v{version}" in changelog


def test_product_release_notes_exist_for_v0_8_0() -> None:
    release_notes = Path("docs/archive/releases/v0.8.0.md").read_text(encoding="utf-8")

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
    assert "changelog.slice(start" in workflow


def test_release_criteria_doc_describes_public_1_0_contract() -> None:
    criteria = Path("docs/implementation/RELEASE_CRITERIA_1_0.md").read_text(encoding="utf-8")
    docs_index = Path("docs/README.md").read_text(encoding="utf-8")

    assert "public release" in criteria
    assert "No telemetry" in criteria
    assert "No cloud sync" in criteria
    assert "does not encrypt captures at rest" in criteria
    assert "Go / no-go gate" in criteria
    assert "RELEASE_CRITERIA_1_0.md" in docs_index


def test_baseline_benchmark_doc_tracks_current_1_0_starting_point() -> None:
    benchmark = Path("docs/archive/implementation_legacy/BENCHMARK_1_0_BASELINE.md").read_text(
        encoding="utf-8"
    )
    docs_index = Path("docs/README.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "v0.9.4" in benchmark
    assert "Windows 11-only" in benchmark
    assert "source-based install" in benchmark
    assert "Scheduler correctness at DST and timezone boundaries" in benchmark
    assert "archive/implementation_legacy/BENCHMARK_1_0_BASELINE.md" in docs_index
    assert "Or from the tray menu: **Reinstall**." in readme
