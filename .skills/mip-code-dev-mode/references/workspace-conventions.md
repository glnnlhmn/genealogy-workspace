<!--Path: .skills/mip-code-dev-mode/references/workspace-conventions.md-->
# Workspace Conventions & Execution Safeguards

Reference specification for `mip-code-dev-mode`. Authoritative directory layout is defined in root `pyproject.toml` and verified via `gd-struct`.

## 1. Path Anchors & Routing

- **Canonical Workspace Root:** `G:/My Drive/genealogy-workspace` (always use forward slashes `/`).
- **Inbound Staging:** `download/` (ingested via `gsi`).
- **Safe Backups:** `archive/backups_<project>/` (timestamped `[filename].[YYYYMMDD_HHMMSS].bk` snapshots).
- **Ephemeral Scratchpad:** `gtemp/` (never `temp/`).
- **Reports:** `reports/` (Radon, structure, and coverage gap reports).
- **Logs:** `logs/` for permanent tools; `gtemp/[script]-timestamp.log` for temporary scripts.
- **Production Data & Profiles:** `data/` (`data/profiles/glenn_profile.json`, `data/profiles/gda_profile.json`).

## 2. Subsystem Coverage Gates

Track both statement and branch coverage via `pytest --cov --cov-branch --cov-report=term-missing` (omit `--basetemp` flags; temporary directory routing is handled in `pyproject.toml`):

| Subsystem | Test Directory | Minimum Statement & Branch Coverage |
| :--- | :--- | :--- |
| `src/ancestry_desk/` | `tests/test_ancestry_desk/` | >= 85.00% |
| `src/gda/` | `tests/test_gda/` | >= 95.00% |
| `src/cli/` | `tests/test_cli/` | >= 95.00% |
| `src/system/` | `tests/test_system/` | 100.00% |
| `src/gen_desk_tools/` | `tests/test_gen_desk_tools/` | 100.00% |

## 3. CLI, Runtime & Safety Standards

- **Runtime & Formatting:** Python 3.13 (`.venv/`), Ruff (`ruff format` + `ruff check --fix`, 100-character max line length), and `mypy` with zero errors.
- **Standard CLI Flags:**
  - `src/gen_desk_tools/`: `-h`/`--help`, `-v`/`--verbose`, `--debug`, `--root`, `--config`, `--prompts` (with standardized `main(argv)`).
  - `src/system/` & `src/cli/`: `-h`/`--help`, `-v`/`--verbose`, `--debug`.
- **Safe I/O & Destructive Guards:**
  - Enforce `encoding="utf-8"` on all file reads and writes.
  - Verify `Path.exists()` before destructive operations (`os.remove`, `shutil.rmtree`) and verify target outputs upon completion.
  - Create atomic pre-write Safe Backups before mutating canonical archive data (`data/`) or tracked source files.
