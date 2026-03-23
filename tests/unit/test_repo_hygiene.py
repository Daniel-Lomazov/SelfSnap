from __future__ import annotations

from pathlib import Path


def test_pytest_artifact_cleanup_script_targets_acl_poisoned_folders() -> None:
    script = Path("scripts/cleanup_pytest_artifacts.ps1").read_text(encoding="utf-8")

    assert "takeown.exe" in script
    assert "icacls.exe" in script
    assert "pytest-cache-files-*" in script
    assert ".pytest_cache" in script
    assert "Test-Administrator" in script
    assert "RepairAcl" in script
    assert "Start-Process" in script
    assert "RunAs" in script
    assert "Elevation returned, but pytest artifact targets still remain." in script


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
    assert "-RepairAcl" in readme
    assert "legacy leftovers" in readme


def test_pytest_config_keeps_temp_output_out_of_repo() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    conftest = Path("tests/conftest.py").read_text(encoding="utf-8")

    assert 'addopts = ["-p", "no:cacheprovider"]' in pyproject
    assert ".pytest_tmp" in pyproject
    assert ".pytest-work" in pyproject
    assert 'Path(local_appdata) / "SelfSnap" / "pytest" / "tmp"' in conftest
