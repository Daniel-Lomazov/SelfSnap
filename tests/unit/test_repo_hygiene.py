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
    assert "UpdateSource" in reinstall
    assert "RelaunchTray" in reinstall
    assert "git pull --ff-only" in reinstall
    assert "VIRTUAL_ENV" in setup
    assert "currently active in this shell" in setup
    assert "another shell or process is using files under" in setup
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
