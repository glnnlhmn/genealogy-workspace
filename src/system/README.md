<!-- Name: README.md -->
<!-- Path: src/system/README.md -->

# System Administration & Developer Utilities (`src/system`)

## Operational Role & Purpose
Workstation administration, script intake pipeline automation, Git hook lifecycle enforcement, database maintenance, and schema compilation.

## Operational Contracts & Quality Gates
System utilities operate under `topic_system_tools.md` and `topic_test_harness.md`:
- **100% Quality Gate**: All modules in `src/system/` must maintain 100.00% statement and branch test coverage.
- **Ruff Compliance**: Strict adherence to Ruff formatting and linting rules pinned to Python 3.13 and a 100-character line length limit.
- **GSI Intake Protection**: Code intake and file movements are automated via `src/system/gsi.py`, enforcing header validation and Safe Backup generation in `archive/backups_system/`.

## Key Tool Inventory
- `gsi.py`: Genealogy Script Importer. Manages validated script intake, header inspection, atomic pre-execution backups, and test runner dispatch (`gsi -r`).
- `install_hooks.py`: Automated installer for Git pre-commit hook wrappers.
- `hooks/pre_commit.py`: Localized staged pre-commit quality engine running Ruff format/lint validation and targeted test execution.
- `db_maintenance.py`: Database maintenance, integrity audits, and vacuum routines.
- `schema_compiler.py`: Schema artifact compilation and model synchronization.