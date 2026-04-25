# User Scripts

These are the supported SelfSnap lifecycle scripts for normal checkout use.

Run them from the repository root:

- `scripts/user/setup.ps1`: create or recreate the repository-local `.venv`, install the package, install dev extras unless `-NoDev` is used, and run `selfsnap doctor`
- `scripts/user/install.ps1`: install SelfSnap from the current checkout for the current user, create the wrapper, sync scheduler state, and update startup integration
- `scripts/user/reinstall.ps1`: refresh the installed state from the current checkout and optionally update the checkout or relaunch the tray
- `scripts/user/uninstall.ps1`: remove the installed wrapper, scheduler tasks, startup shortcut, and optionally SelfSnap-owned user data

Typical sequence:

1. `powershell -ExecutionPolicy Bypass -File .\scripts\user\setup.ps1`
2. `powershell -ExecutionPolicy Bypass -File .\scripts\user\install.ps1`
3. `SelfSnap tray`

If SelfSnap is already installed, prefer the wrapper commands such as `SelfSnap reinstall` and `SelfSnap uninstall` unless you specifically need to invoke the PowerShell script entrypoint.
