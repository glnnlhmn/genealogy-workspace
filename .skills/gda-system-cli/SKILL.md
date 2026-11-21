<!--Path: .skills/gda-system-cli/SKILL.md-->
---
name: gda-system-cli
description: Architecture and quality gates for Git hook plumbing (src/system/) and operational CLI orchestrators (src/cli/) in the genealogy workspace. Use whenever working on Git hooks, hook installers, or operational CLI tools that mutate canonical archive data.
---

# GDA System and Operational CLI Standards

Governance for repository Git plumbing (`src/system/`) and operational CLI orchestrators (`src/cli/`).

## When to Use

- Editing or testing Git hooks and hook installers under `src/system/` or `tests/test_system/`.
- Building, migrating, or testing operational CLI tools under `src/cli/` or `tests/test_cli/`.

## 1. System Plumbing (`src/system/`)

`src/system/` is strictly scoped to Git hook automation and workstation onboarding:

- `src/system/hooks/pre_commit.py`: Inspects staged files via `git diff --cached --name-only`, enforces Ruff formatting and linting, and dispatches localized pytest runs (`-t`/`--target`, `-a`/`--all`).
- `src/system/hooks/pre_push.py`: Pre-push repository verification hook.
- `src/system/install_hooks.py`: Deploys POSIX-compliant Git hook wrappers under `.git/hooks/` with executable permissions.

**Invariants:**

- Resolve paths dynamically relative to the workspace root for Windows and POSIX portability.
- Provide `-h`/`--help`, `-v`/`--verbose`, and `--debug`, routing logs to `logs/` or standard streams.
- Enforce strict 100.00% statement and branch coverage under `tests/test_system/`.

## 2. Operational CLI Orchestrators (`src/cli/`)

`src/cli/` houses production CLI entrypoints with read/write authority over canonical archive data (`data/`) and databases:

- Consume shared domain libraries from `src/gda/` rather than duplicating domain logic.
- Trigger atomic pre-write Safe Backups in `archive/backups_cli/` via `gda.io` before mutating canonical data stores.
- Implement standard `argparse` flags (`-h`/`--help`, `-v`/`--verbose`, `--debug`) and route execution logs to `logs/`.
- Enforce >= 95.00% statement and branch coverage under `tests/test_cli/`.

## Gotchas

- General developer workstation tools (intake, backups, metrics, README generation, structure checks) belong in `src/gen_desk_tools/`, not `src/system/` or `src/cli/`.
