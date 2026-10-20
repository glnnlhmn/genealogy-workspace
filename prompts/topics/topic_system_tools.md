<!--Path: prompts/topics/topic_system_tools.md-->
# Topic Specification: System Utility Architecture (`src/system/`)
<!-- Version: 1.1.0 -->
<!-- Operational Directive: Ingest this topic specification as a modular overlay extending the active MIP baseline. Do not execute or rewrite without explicit operator command. Confirm processing and state any conflicts. -->

## 1. Architectural Scope & Operational Role
System utilities under `src/system/` govern developer workstation environment configuration, Git hook deployment, script intake, and structure verification. Unlike operational tools that mutate canonical genealogical domain data (`data/`), system utilities maintain local environment consistency, enforce workflow automation, and ensure repository onboarding integrity.

## 2. Production System Utility Inventory & Contracts

### 2.1 Genealogy Script Importer (`src/system/gsi.py`)
* **Role:** Automated native code and asset intake engine.
* **Intake Pipeline:** Inspects candidate files in `download/`, extracts destination paths from Line 1/2 `Path: [relative/path]` docstring declarations, creates atomic pre-write Safe Backups in `archive/backups_[project]/`, relocates files to their canonical destinations, and triggers pytest verification.
* **CLI Flags:** Standard interface supporting `-h`/`--help`, `-f`/`--force`, `-r`/`--run`, `-c`/`--clean`, and `-p`/`--prefix`.
* **Execution Alias:** Bound in `~/.bashrc` via `alias gsi="python src/system/gsi.py"`.

### 2.2 Pre-Commit Hook Runner (`src/system/hooks/pre_commit.py`)
* **Role:** Staged and targeted pre-commit test and linting orchestrator.
* **Operational Scope:** Inspects staged files via `git diff --cached --name-only`, enforces Ruff formatting and linting inspections, and dispatches localized pytest runs.
* **CLI Flags:** Supports `-h`/`--help`, component targeting via `-t`/`--target`, and full test execution via `-a`/`--all`.

### 2.3 Hook Installer (`src/system/install_hooks.py`)
* **Role:** Automated workstation onboarding and Git hook deployer.
* **Deployment Contract:** Generates POSIX-compliant pre-commit wrappers at `.git/hooks/pre-commit` and grants executable bit permissions (`chmod +x`).

## 3. Mandatory System Utility Invariants
* **PEP 440 Module Versioning:** Every utility must declare a module-level `__version__` string conforming to PEP 440 local build identifiers using monotonic cumulative counters (`<major>.<minor>.<rev>+build.<counter>`).
* **Workstation & OS Portability:** Utilities must execute hermetically across Windows and POSIX developer environments without hardcoded user-profile dependencies, resolving boundaries dynamically relative to the workspace root anchor.
* **CLI Interface & Logging:** Permanent utilities implement standard `argparse` flags for `-h`/`--help`, `-v`/`--verbose`, and `--debug`, emitting runtime execution logs strictly to `logs/` or standard streams. Temporary utilities do not require logging, but if required, logs route to `gtemp/`.

## 4. Verification Harness & Coverage Quality Gate
* **Test Placement:** System utilities must be validated by dedicated standalone test suites located strictly under `tests/test_system/` (e.g., `tests/test_system/test_gsi.py`, `tests/test_system/test_install_hooks.py`).
* **Quality Gate:** Strict **100.00%** statement and branch coverage required before release.
* **Hermetic Sandboxing:** All mutations must execute inside isolated pytest sandboxes (`tmp_path` / `--basetemp=gtemp/pytest_tmp`).