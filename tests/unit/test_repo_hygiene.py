from __future__ import annotations

from pathlib import Path


def test_repo_artifact_cleanup_script_targets_acl_poisoned_folders() -> None:
    script = Path("scripts/developer/cleanup_repo_artifacts.ps1").read_text(encoding="utf-8")

    assert "takeown" in script
    assert "icacls" in script
    assert ".pytest_cache" in script
    assert "cov_annotate" in script
    assert "RepairAcl" in script
    assert "Get-ArtifactCandidates" in script
    assert "Remove-Artifact" in script
    assert "Remove-Item" in script


def test_install_and_uninstall_scripts_support_interpreter_overrides() -> None:
    helpers = Path("scripts/shared/_selfsnap_script_helpers.ps1").read_text(encoding="utf-8")
    install = Path("scripts/user/install.ps1").read_text(encoding="utf-8")
    reinstall = Path("scripts/user/reinstall.ps1").read_text(encoding="utf-8")
    setup = Path("scripts/user/setup.ps1").read_text(encoding="utf-8")
    uninstall = Path("scripts/user/uninstall.ps1").read_text(encoding="utf-8")
    build = Path("scripts/developer/build.ps1").read_text(encoding="utf-8")
    smoke = Path("scripts/developer/smoke_test.ps1").read_text(encoding="utf-8")
    scripts_readme = Path("scripts/README.md").read_text(encoding="utf-8")
    user_readme = Path("scripts/user/README.md").read_text(encoding="utf-8")
    developer_readme = Path("scripts/developer/README.md").read_text(encoding="utf-8")

    assert "function Resolve-PythonPath" in helpers
    assert "function Resolve-PythonwPath" in helpers
    assert "function Get-UvCommand" in helpers
    assert "..\\shared\\_selfsnap_script_helpers.ps1" in install
    assert "..\\shared\\_selfsnap_script_helpers.ps1" in reinstall
    assert "..\\shared\\_selfsnap_script_helpers.ps1" in setup
    assert "..\\shared\\_selfsnap_script_helpers.ps1" in uninstall
    assert "..\\shared\\_selfsnap_script_helpers.ps1" in build
    assert "..\\shared\\_selfsnap_script_helpers.ps1" in smoke
    assert "PythonwExe" in install
    assert "Get-InstalledSchemaSupport" in install
    assert "Scheduler sync and startup shortcut updates were " in install
    assert "skipped to avoid rewriting a newer config with an older checkout" in install
    assert "UpdateSource" in reinstall
    assert "RelaunchTray" in reinstall
    assert "git pull --ff-only" in reinstall
    assert "VIRTUAL_ENV" in setup
    assert "--allow-existing" in setup
    assert "uv venv in-place recovery" in setup
    assert "Retrying in place with --allow-existing" in setup
    assert "Stop-LockingVenvToolProcesses" in setup
    assert "ruff.exe" in setup
    assert "pip install --python $venvPython" in setup
    assert "uv runtime install" in setup
    assert "uv dev install" in setup
    assert "before development extras attempt $attempt" in setup
    assert "Development extras install attempt $attempt failed" in setup
    assert "Runtime setup succeeded, but development extras could not be fully refreshed" in setup
    assert "currently active in this shell" in setup
    assert "appear to be locked" in setup
    assert "PythonExe" in uninstall
    assert "Get-TrustedInstallMetadata" in uninstall
    assert "RemoveUserData" in uninstall
    assert "Stop-RunningSelfSnapTray" in uninstall
    assert "Get-InvokingTrayProcessId" in uninstall
    assert "Stop-Process -Id $process.ProcessId -Force" in uninstall
    assert build.lstrip().startswith("param(")
    assert "SkipInstall" in smoke
    assert "scripts/user/setup.ps1" in scripts_readme
    assert "scripts/developer/cleanup_repo_artifacts.ps1" in scripts_readme
    assert "scripts/user/README.md" in scripts_readme
    assert "scripts/developer/README.md" in scripts_readme
    assert "scripts/user/setup.ps1" in user_readme
    assert "scripts/user/install.ps1" in user_readme
    assert "scripts/developer/build.ps1" in developer_readme
    assert "scripts/developer/cleanup_repo_artifacts.ps1" in developer_readme


def test_readme_documents_cleanup_workflow() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "scripts/developer/cleanup_repo_artifacts.ps1" in readme
    assert "scripts/user/setup.ps1" in readme
    assert "scripts/user/README.md" in readme
    assert "scripts/developer/README.md" in readme
    assert "pytest-cache-files-*" in readme
    assert "pytest cache provider is disabled" in readme.lower()
    assert "-RepairAcl" in readme
    assert "cov_annotate" in readme


def test_docs_readme_network_links_navigation_hubs() -> None:
    root_readme = Path("README.md").read_text(encoding="utf-8")
    docs_readme = Path("docs/README.md").read_text(encoding="utf-8")
    user_readme = Path("docs/user/README.md").read_text(encoding="utf-8")
    developer_readme = Path("docs/developer/README.md").read_text(encoding="utf-8")
    archive_readme = Path("docs/archive/README.md").read_text(encoding="utf-8")
    customer_baseline_readme = Path("docs/archive/customer_baseline/README.md").read_text(
        encoding="utf-8"
    )
    starter_kit_readme = Path("docs/archive/starter_kit/README.md").read_text(
        encoding="utf-8"
    )
    releases_readme = Path("docs/archive/releases/README.md").read_text(encoding="utf-8")
    planning_baseline_readme = Path(
        "docs/archive/v1_0_planning_baseline/README.md"
    ).read_text(encoding="utf-8")

    assert "[docs/README.md](docs/README.md)" in root_readme
    assert "[docs/user/README.md](docs/user/README.md)" in root_readme
    assert "[docs/developer/README.md](docs/developer/README.md)" in root_readme
    assert "[docs/archive/README.md](docs/archive/README.md)" in root_readme
    assert "Documentation sync points" in root_readme

    assert "[../README.md](../README.md)" in docs_readme
    assert "[user/README.md](user/README.md)" in docs_readme
    assert "[developer/README.md](developer/README.md)" in docs_readme
    assert "[archive/README.md](archive/README.md)" in docs_readme
    assert "Keep These In Sync" in docs_readme

    assert "[../../README.md](../../README.md)" in user_readme
    assert "[../README.md](../README.md)" in user_readme
    assert "[../developer/README.md](../developer/README.md)" in user_readme
    assert "Keep These In Sync" in user_readme

    assert "[../../README.md](../../README.md)" in developer_readme
    assert "[../README.md](../README.md)" in developer_readme
    assert "[../user/README.md](../user/README.md)" in developer_readme
    assert "Keep These In Sync" in developer_readme

    assert "[../../README.md](../../README.md)" in archive_readme
    assert "[../README.md](../README.md)" in archive_readme
    assert "[customer_baseline/README.md](customer_baseline/README.md)" in archive_readme
    assert "[starter_kit/README.md](starter_kit/README.md)" in archive_readme
    assert "[releases/README.md](releases/README.md)" in archive_readme
    assert "Keep These In Sync" in archive_readme

    assert "[../../../README.md](../../../README.md)" in customer_baseline_readme
    assert "[../../README.md](../../README.md)" in customer_baseline_readme
    assert "[../README.md](../README.md)" in customer_baseline_readme

    assert "[../../../README.md](../../../README.md)" in starter_kit_readme
    assert "[../../README.md](../../README.md)" in starter_kit_readme
    assert "[../README.md](../README.md)" in starter_kit_readme

    assert "[../../../README.md](../../../README.md)" in releases_readme
    assert "[../../README.md](../../README.md)" in releases_readme
    assert "[../README.md](../README.md)" in releases_readme

    assert "[../../../README.md](../../../README.md)" in planning_baseline_readme
    assert "[../../README.md](../../README.md)" in planning_baseline_readme
    assert "[../README.md](../README.md)" in planning_baseline_readme


def test_docs_call_out_stable_posture_and_setup_lock_recovery() -> None:
    root_readme = Path("README.md").read_text(encoding="utf-8").lower()
    docs_readme = Path("docs/README.md").read_text(encoding="utf-8").lower()
    user_readme = Path("docs/user/README.md").read_text(encoding="utf-8").lower()
    install_doc = Path("docs/user/INSTALL_AND_UPDATE.md").read_text(encoding="utf-8")
    troubleshooting_doc = Path("docs/user/TROUBLESHOOTING.md").read_text(
        encoding="utf-8"
    )
    script_readme = Path("scripts/user/README.md").read_text(encoding="utf-8")

    assert "stable public release line" in root_readme
    assert "stable public release line" in docs_readme
    assert "stable public release line" in user_readme
    assert "stable public release line" in install_doc.lower()
    assert "uv venv --allow-existing" in install_doc
    assert "ruff.exe" in install_doc
    assert "newer schema than the current checkout supports" in install_doc.lower()
    assert "scheduler sync and startup shortcut updates" in install_doc.lower()
    assert "access denied under `.venv\\Scripts`" in troubleshooting_doc
    assert "uv venv --allow-existing" in troubleshooting_doc
    assert "ruff.exe" in troubleshooting_doc
    assert "config `schema_version` is newer than this checkout" in troubleshooting_doc
    assert "stable public release line" in script_readme.lower()


def test_pytest_config_keeps_temp_output_out_of_repo() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    conftest = Path("tests/conftest.py").read_text(encoding="utf-8")

    assert '"-p", "no:cacheprovider"' in pyproject
    assert ".pytest_tmp" in pyproject
    assert ".pytest-work" in pyproject
    assert 'Path(local_appdata) / "SelfSnap" / "pytest" / "tmp"' in conftest


def test_repo_contains_github_automation_for_ci_and_issue_intake() -> None:
    ci = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    intake = Path(".github/workflows/issue-intake.yml").read_text(encoding="utf-8")

    assert "windows-latest" in ci
    assert "compileall src tests" in ci
    assert "pytest -q" in ci
    assert "actions/github-script" in intake
    assert "ready-for-local-planning" in intake
    assert "selfsnap-planning-intake" in intake


def test_readme_documents_issue_reporting_and_github_workflows() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Report Issue" in readme
    assert "SELFSNAP_GITHUB_REPO" in readme
    assert "offline by default" in readme.lower()
    assert "no telemetry" in readme.lower()
    assert "issue-intake" in readme
