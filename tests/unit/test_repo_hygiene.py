from __future__ import annotations

from pathlib import Path


def test_pytest_artifact_cleanup_script_targets_acl_poisoned_folders() -> None:
    script = Path("scripts/cleanup_pytest_artifacts.ps1").read_text(encoding="utf-8")

    assert "takeown.exe" in script
    assert "icacls.exe" in script
    assert "pytest-cache-files-*" in script
    assert ".pytest_cache" in script
    assert "Test-Administrator" in script


def test_install_and_uninstall_scripts_support_interpreter_overrides() -> None:
    install = Path("scripts/install.ps1").read_text(encoding="utf-8")
    uninstall = Path("scripts/uninstall.ps1").read_text(encoding="utf-8")

    assert "PythonwExe" in install
    assert "Resolve-PythonPath" in install
    assert "PythonExe" in uninstall
    assert "Get-TrustedInstallMetadata" in uninstall


def test_readme_documents_pytest_hygiene_workflow() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "cleanup_pytest_artifacts.ps1" in readme
    assert "pytest-cache-files-*" in readme
    assert "pytest cache provider is disabled" in readme.lower()
