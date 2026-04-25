# Scripts

SelfSnap separates script entrypoints by audience:

- `user/`: supported lifecycle and install commands for everyday checkout use
- `developer/`: repo hygiene, packaging, validation, and publishing helpers
- `shared/`: internal helper code sourced by the script entrypoints

Folder guides:

- `scripts/user/README.md`: user-facing setup, install, reinstall, and uninstall entrypoints
- `scripts/developer/README.md`: developer-only cleanup, packaging, smoke-test, and publishing helpers

User-facing automation:

- `scripts/user/setup.ps1`
- `scripts/user/install.ps1`
- `scripts/user/reinstall.ps1`
- `scripts/user/uninstall.ps1`

Developer-only automation:

- `scripts/developer/build.ps1`
- `scripts/developer/smoke_test.ps1`
- `scripts/developer/cleanup_pytest_artifacts.ps1`
- `scripts/developer/cleanup_repo_artifacts.ps1`
- `scripts/developer/publish_github_metadata.ps1`

Run all scripts from the repository root unless a script documents otherwise.