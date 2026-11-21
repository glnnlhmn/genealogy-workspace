<!--Path: .skills/gen-desk-tools/SKILL.md-->
---
name: gen-desk-tools
description: Architecture, shared core primitives, configuration model (pyproject.toml + gda_conf.toml), and CLI conventions for src/gen_desk_tools/ (GDT). Use whenever building, migrating, refactoring, or testing workstation tools under src/gen_desk_tools/ or tests/test_gen_desk_tools/.
---

# GenDesk Tools (GDT) Architecture

Modular developer and workstation automation suite under `src/gen_desk_tools/`.

## When to Use

- Designing or building shared primitives in `src/gen_desk_tools/core/`.
- Maintaining or refactoring workstation tools (`backup_mgr`, `coverage_gaps`, `metrics`, `radon_report`, `readme_gen`, `script_importer`, `structure`, `menu`).
- Configuring `[project.scripts]` entrypoints in `pyproject.toml` or runtime settings in `gda_conf.toml`.

## Package Layout and Short CLI Commands

Expose descriptive subpackages under `src/gen_desk_tools/` and bind short terminal commands via `[project.scripts]` in `pyproject.toml`:

- `src/gen_desk_tools/core/`: Shared internal library (workspace root resolution, centralized `MODE_TARGETS`, TOML config loader, atomic file writes, Safe Backup routing, CLI/logging helpers).
- `src/gen_desk_tools/script_importer/`: Native file intake engine (`gsi`).
- `src/gen_desk_tools/backup_mgr/`: Safe Backup creation, 4-section audit, pruning, and restoration (`gdb`).
- `src/gen_desk_tools/coverage_gaps/`: Pytest missing-line and branch gap extractor (`gd-gaps`).
- `src/gen_desk_tools/metrics/`: Radon, pytest coverage, mypy, Ruff, hygiene, and import-graph telemetry (`gd-metrics`).
- `src/gen_desk_tools/radon_report/`: Combined Radon complexity and maintainability reporter (`gdradon`).
- `src/gen_desk_tools/readme_gen/`: AST-driven package `README.md` generator (`gdrm`).
- `src/gen_desk_tools/structure/`: Workspace structure verifier (`gd-struct`).
- `src/gen_desk_tools/menu.py`: Layered interactive console menu (`gd-menu`).

## Configuration Model

- Define package metadata and `[project.scripts]` entrypoints in root `pyproject.toml`.
- Support runtime defaults in `[tool.gen_desk_tools]` (`pyproject.toml`) with optional overrides in root `gda_conf.toml`.

## Mandatory Invariants

- **Uniform Package Layout:** Every executable subpackage provides `__init__.py`, `__main__.py`, `cli.py` (with standardized `main(argv)`), `README.md`, and focused submodules to keep Radon cyclomatic complexity at Grade A or B.
- **CLI and Logging:** Implement standard `argparse` flags (`-h`/`--help`, `-v`/`--verbose`, `--debug`, `--root`, `--config`, `--prompts`) and route persistent logs to `logs/`.
- **Safe Backup Routing:** Pre-write backups for GDT source and tests route to `archive/backups_gen_desk_tools/`.
- **Quality Gate:** Maintain co-located tests under `tests/test_gen_desk_tools/` achieving strict 100.00% statement and branch coverage and 0 mypy/Ruff errors.

## Gotchas

- Keep Git hook plumbing (`pre_commit.py`, `pre_push.py`, `install_hooks.py`) in `src/system/`, not in `src/gen_desk_tools/`.
