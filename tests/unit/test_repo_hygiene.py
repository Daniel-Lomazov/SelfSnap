from __future__ import annotations

from pathlib import Path


def test_repo_artifact_cleanup_script_targets_acl_poisoned_folders() -> None:
    script = Path("scripts/cleanup_repo_artifacts.ps1").read_text(encoding="utf-8")

    assert "takeown" in script
    assert "icacls" in script
    assert ".pytest_cache" in script
    assert "cov_annotate" in script
    assert "RepairAcl" in script
    assert "Get-ArtifactCandidates" in script
    assert "Remove-Artifact" in script
    assert "Remove-Item" in script


def test_install_and_uninstall_scripts_support_interpreter_overrides() -> None:
    install = Path("scripts/install.ps1").read_text(encoding="utf-8")
    reinstall = Path("scripts/reinstall.ps1").read_text(encoding="utf-8")
    uninstall = Path("scripts/uninstall.ps1").read_text(encoding="utf-8")

    assert "PythonwExe" in install
    assert "Resolve-PythonPath" in install
    assert "UpdateSource" in reinstall
    assert "RelaunchTray" in reinstall
    assert "git pull --ff-only" in reinstall
    assert "PythonExe" in uninstall
    assert "Get-TrustedInstallMetadata" in uninstall
    assert "RemoveUserData" in uninstall
    assert "Stop-RunningSelfSnapTray" in uninstall
    assert "Get-InvokingTrayProcessId" in uninstall
    assert "Stop-Process -Id $process.ProcessId -Force" in uninstall


def test_readme_documents_cleanup_workflow() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "cleanup_repo_artifacts.ps1" in readme
    assert "pytest-cache-files-*" in readme
    assert "pytest cache provider is disabled" in readme.lower()
    assert "-RepairAcl" in readme
    assert "cov_annotate" in readme


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
