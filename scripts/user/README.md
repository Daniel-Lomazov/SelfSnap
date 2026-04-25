# User Scripts

These are the supported SelfSnap lifecycle scripts for normal checkout use.
They support the current preview build, not a stable release.

Run them from the repository root:

- `scripts/user/setup.ps1`: create or recreate the repository-local `.venv`, stop known background tool executables from `.venv\Scripts`, retry in place with `uv venv --allow-existing` if cleanup is locked, make the runtime environment usable, and warn if locked developer tooling prevents a full dev-extras refresh unless `-NoDev` is used
- `scripts/user/install.ps1`: install SelfSnap from the current checkout for the current user, create the wrapper, sync scheduler state, and update startup integration
- `scripts/user/reinstall.ps1`: refresh the installed state from the current checkout and optionally update the checkout or relaunch the tray
- `scripts/user/uninstall.ps1`: remove the installed wrapper, scheduler tasks, startup shortcut, and optionally SelfSnap-owned user data

Typical sequence:

1. `powershell -ExecutionPolicy Bypass -File .\scripts\user\setup.ps1`
2. `powershell -ExecutionPolicy Bypass -File .\scripts\user\install.ps1`
3. `SelfSnap tray`

If SelfSnap is already installed, prefer the wrapper commands such as `SelfSnap reinstall` and `SelfSnap uninstall` unless you specifically need to invoke the PowerShell script entrypoint.
