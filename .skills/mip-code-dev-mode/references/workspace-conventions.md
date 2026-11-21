<!--Path: .skills/mip-code-dev-mode/references/workspace-conventions.md-->
# Workspace Conventions & Execution Safeguards

Reference specification for `mip-code-dev-mode`. Authoritative directory layout comes from `pyproject.toml` and `gd-struct`.

## Path Anchors

- **Workspace Root:** `G:/My Drive/genealogy-workspace` (forward slashes `/`).
- **Staging (`gsi`):** `download/` .
- **Safe Backups:** `archive/backups_<project>/` (`[filename].[YYYYMMDD_HHMMSS].bk`).
- **Scratchpad:** `gtemp/` (never `temp/`).
- **Reports:** `reports/`.
- **Logs:** `logs/` for permanent tools; `gtemp/[script]-timestamp.log` for temporary scripts.
- **Data & Profiles:** `data/` (`data/profiles/glenn_profile.json`, `data/profiles/gda_profile.json`).

## Coverage Gates

Verify statement and branch coverage via `pytest --cov --cov-branch --cov-report=term-missing` (omit `--basetemp` flags; temporary paths are configured in `pyproject.toml`):

| Subsystem | Test Directory | Minimum Statement & Branch Coverage |
| :--- | :--- | :--- |
| `src/ancestry_desk/` | `tests/test_ancestry_desk/` | >= 85.00% |
| `src/gda/` | `tests/test_gda/` | >= 95.00% |
| `src/cli/` | `tests/test_cli/` | >= 95.00% |
| `src/system/` | `tests/test_system/` | 100.00% |
| `src/gen_desk_tools/` | `tests/test_gen_desk_tools/` | 100.00% |

## Execution Safeguards

- **Toolchain:** Python 3.13 (`.venv/`), Ruff (`ruff format` + `ruff check --fix`, 100-char line limit), and `mypy` with zero errors.
- **CLI Flags:** `-h`/`--help`, `-v`/`--verbose`, `--debug` across CLIs, plus `--root`, `--config`, `--prompts` for `src/gen_desk_tools/` (`main(argv)`).
- **File & Destructive Safety:** Use `encoding="utf-8"`, check `Path.exists()` before destructive operations (`os.remove`, `shutil.rmtree`), verify outputs after completion, and take atomic pre-write Safe Backups before mutating canonical archive data (`data/`) or tracked source files.
- **Test Collection Shielding:** Set `<Class>.__test__ = False` or alias `Test*` domain types imported into test files so pytest does not collect them as tests.
