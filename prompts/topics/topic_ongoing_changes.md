<!--Path: prompts/topics/topic_ongoing_changes.md-->
# Topic Specification: Ongoing Project Topology & Architecture Migration

## 1. Architectural Migration Summary
This document tracks the transitional changes applied to modernize workspace topology, development tooling, and verification automation away from legacy tools/ structures toward a standardized, PEP 517/621-compliant layout.

## 2. Workspace Root & Directory Re-Anchoring
* **Canonical Root Anchor:** Relocated from `G:/My Drive/genealogy-digital-archive` to `G:/My Drive/genealogy-workspace`.
* **Standardized Package Directory Topology (`src/`):**
  * `tools/sys/` -> `src/system/` (Workstation administration, script intake automation, Git hook installation).
  * `tools/ops/` -> `src/cli/` (Operational CLI orchestrators and administrative entrypoints).
  * `tools/lib/` -> `src/gda/` (Decoupled core domain libraries, reference resolution, and schema engines).
  * Presentation Layer: Added `src/ancestry_desk/` (Desktop application presentation layer, state management, controllers, views).
* **Storage Re-Mapping:**
  * `import/` -> `download/` (Inbound staging directory for untracked assets and script intake).
* `backups/` -> `archive/` (Isolated Safe Backup directories: `archive/backups_[project]/`).
  * `gtemp/` (Ephemeral scratchpad, temporary artifacts, and pytest sandbox `--basetemp=gtemp/pytest_tmp`).

## 3. Tooling Standard: Python 3.13 & Ruff Integration
* **Target Runtime:** Python 3.13.x virtual environment (`.venv/`).
* **Linter & Formatter (ruff):**
  * Fully replaces legacy Flake8, Black, and isort configurations.
  * Line length pinned to 100 characters in `pyproject.toml`.
  * Target Python version set to `py313`.
  * Pre-commit verification: Enforces `ruff format --check` and `ruff check`.
* **Testing Engine (pytest):**
  * Branch and statement coverage tracked via `pytest-cov` across tiered subsystem gates:
    * `src/ancestry_desk/`: Baseline threshold >= 85.00%.
    * `src/gda/`, `src/cli/`: Minimum threshold >= 95.00%.
    * `src/system/`: Strict threshold 100.00%.
  * Marker taxonomy streamlined to 5 active markers (`unit`, `regression`, `integration`, `integrity`, `smoke`), with obsolete `burnin` and `slow` markers pruned.
  * Root pytest execution routed to `gtemp/pytest_tmp` to eliminate Windows file-locking collisions.

## 4. Automation & Git Hook Infrastructure
* **Genealogy Script Importer (GSI) (`src/system/gsi.py`):**
  * Hermetic intake runner inspecting candidate in-docstring metadata (`Path: [relative/path]`).
  * Enforces Safe Backup generation into `archive/backups_<project>/` prior to overwriting code.
  * Standard CLI interface supporting `-h`/`--help`, `-f`/`--force`, `-r`/`--run`, `-c`/`--clean`, and `-p`/`--prefix`.
  * Shell alias mapped in `~/.bashrc`: `alias gsi="python src/system/gsi.py"`.
* **Staged & Component-Targeted Pre-Commit Hook (`src/system/hooks/pre_commit.py`):**
  * Analyzes staged changes via `git diff --cached --name-only`.
  * Supports explicit folder/component targeting via `-t`/`--target`.
  * Supports complete workspace test runs via `-a`/`--all`.
  * Executes fast Ruff format/lint inspections prior to dispatching localized unit or integration pytest targets.
* **Hook Deployment Utility (`src/system/install_hooks.py`):**
  * Automated deployer generating POSIX-compliant wrapper at `.git/hooks/pre-commit`.
  * Grants executable bit permissions (`chmod +x`).

## 5. Version Control & Staging Governance
* **Standardized .gitignore:**
  * Hierarchical organization (OS artifacts -> IDE -> Python runtime -> Quality gates -> Ephemeral workspace -> Data isolation).
  * Directory retention via `.gitkeep` for empty tracking (`download/`, `gtemp/`, `logs/`, `reports/`, `archive/backups_*/`).
  * `prompts/` maintained strictly under active Git version control.