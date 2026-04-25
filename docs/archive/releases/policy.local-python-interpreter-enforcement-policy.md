# Policy: Interpreter Enforcement And Local Venv

[ARCHIVED RELEASE]
This file is part of the archived release pack indexed in [README.md](README.md).
It preserves historical release-specific policy guidance and is not the active product or maintainer contract.

This policy defines the interpreter contract for source-based runs and the user guidance required when that contract is broken.

## Policy

Source-based runs must execute with the checkout-local `.venv` interpreter.

## Why

- Prevent drift between globally installed Python and project dependencies.
- Ensure tray/worker behavior matches tested environment assumptions.
- Avoid accidental execution under unsupported interpreter/runtime combinations.

## Enforcement expectations

- Foreground launch paths prefer local `.venv` and may redirect when launched from another interpreter.
- Background launch paths resolve through the same local-interpreter contract.
- If `.venv` is missing, user-facing guidance must point to setup commands.

## User guidance contract

When local `.venv` is unavailable, docs and CLI messaging should direct users to:

1. `powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1`
2. `powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1`

## Validation

- Unit tests should cover allow/redirect/block behavior.
- Manual checks should validate tray start and manual capture from local `.venv`.
