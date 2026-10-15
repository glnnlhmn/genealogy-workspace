<!--
Name: topic_ongoing_changes.md
Path: prompts/topics/topic_ongoing_changes.md
-->
# Topic Specification: Ongoing Project Topology & Architecture Migration
<!-- Version: 1.0.0 -->
<!-- Operational Directive: Ingest this topic specification as a modular overlay extending the active MIP baseline. Do not execute or rewrite without explicit operator command. Confirm processing and state any conflicts. -->

## 1. Architectural Migration Summary
This document tracks the transitional changes applied to modernize the workspace topology, development tooling, and verification automation away from legacy `tools/` and `gtemp/` structures toward a standardized, PEP 517/621-compliant layout.

---

## 2. Workspace Root & Directory Re-Anchoring

* **Canonical Root Anchor:** Relocated from `G:/My Drive/genealogy-digital-archive` to `G:/My Drive/genealogy-workspace`.
* **Standardized Package Directory Topology (`src/`):**
  * `tools/sys/` $\rightarrow$ `src/system/` (Workstation administration, script intake automation, Git hook installation).
  * `tools/ops/` $\rightarrow$ `src/cli/` (Operational CLI orchestrators and administrative entrypoints).
  * `tools/lib/` $\rightarrow$ `src/gda/` and `src/ancestry_desk/` (Decoupled core domain libraries, reference resolution, and schema engines).
* **Ephemeral & Storage Re-Mapping:**
  * `gtemp/` $\rightarrow$ `temp/` (Runtime scratchpad, temporary artifacts, and pytest sandbox `--basetemp=temp/pytest_tmp`).
  * `import/` $\rightarrow$ `download/` (Inbound staging directory for untracked assets and script intake).
  * `backups/` $\rightarrow$ `archive/` (Isolated Safe Backup directories: `archive/backups_system/`, `archive/backups_gda/`, etc.).

---

## 3. Tooling Standard: Python 3.13 & Ruff Integration

* **Target Runtime:** Python 3.13.x virtual environment (`.venv/`).
* **Linter & Formatter (`ruff`):**
  * Fully replaces legacy Flake8, Black, and isort configurations.
  * Line length pinned to 100 characters in `pyproject.toml`.
  * Target Python version set to `py313`.
  * Pre-commit verification: Enforces `ruff format --check` and `ruff check`.
* **Testing Engine (`pytest`):**
  * Branch and statement coverage tracked via `pytest-cov`.
  * System tools (`src/system/`) enforce a 100.00% statement and branch coverage gate.
  * Root pytest execution routed to `temp/pytest_tmp` to eliminate Windows file-locking collisions.

---

## 4. Automation & Git Hook Infrastructure

* **Genealogy Script Importer (GSI) (`src/system/gsi.py`):**
  * Hermetic intake runner inspecting candidate headers (`# Name:`, `# Path:`, or JSON metadata).
  * Enforces Safe Backup generation into `archive/backups_<project>/` prior to overwriting code.
  * Standard CLI interface supporting `-h`/`--help`, `-f`/`--force`, `-r`/`--run`, `-c`/`--clean`, and `-p`/`--prefix`.
  * Shell alias mapped in `~/.bashrc`: `alias gsi="python src/system/gsi.py"`.
* **Staged & Component-Targeted Pre-Commit Hook (`src/system/hooks/pre_commit.py`):**
  * Analyzes staged changes via `git diff --cached --name-only`.
  * Supports explicit folder/component targeting via `-t`/`--target` (e.g., `-t src/system`).
  * Supports complete workspace test runs via `-a`/`--all`.
  * Executes fast Ruff format/lint inspections prior to dispatching localized `smoke or unit` pytest targets.
* **Hook Deployment Utility (`src/system/install_hooks.py`):**
  * Automated deployer generating the POSIX-compliant bash wrapper at `.git/hooks/pre-commit`.
  * Grants executable bit permissions (`chmod +x`).

---

## 5. Version Control & Staging Governance

* **Standardized `.gitignore`:**
  * Hierarchical organization (OS artifacts $\rightarrow$ IDE $\rightarrow$ Python runtime $\rightarrow$ Quality gates $\rightarrow$ Ephemeral workspace $\rightarrow$ Data isolation).
  * Directory retention via `.gitkeep` for empty tracking (`download/`, `temp/`, `logs/`, `reports/`, `archive/backups_*/`).
  * `prompts/` maintained strictly under active Git version control.