<!-- Name: README.md -->
<!-- Path: src/cli/README.md -->

# Operational Command-Line Orchestrators (`src/cli`)

## Operational Role & Purpose
Permanent command-line interface tools providing administrative orchestration, data ingestion, pipeline control, and operational mutations across digital archive registries (`data/entities/`) and secondary indices (`data/indexes/`).

## Architectural Governance & Contracts
All CLI orchestrators within this directory operate under `topic_operational_tools.md`:
- **File-Level Metadata**: Lines 1–2 define `# Name: [filename]` and `# Path: [relative_path]`.
- **Versioning**: Declares `__version__` adhering to PEP 440 with monotonic build increments (`<major>.<minor>.<rev>+build.r<counter>`).
- **Standard Arguments**: Implements standard argparse flags for `-h/--help`, `--debug`, and `-v/--verbose`.
- **Safe Backup Protocol**: Enforces atomic pre-execution backups in `archive/backups_cli/` before performing stateful writes or mutations on core data stores.
- **Logging**: Automatically routes structured runtime logs to `logs/[tool-name]-[timestamp].log`.

## Directory Layout
- `main.py`: Primary dispatch router and unified CLI entrypoint.
- `commands/`: Individual operational command handlers and transactional task scripts.
- `formatters/`: Terminal output formatters, table printers, and report presentation utilities.