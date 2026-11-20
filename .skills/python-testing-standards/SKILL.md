---
name: python-testing-standards
description: Universal Python pytest architecture, 5-marker taxonomy, 6-group section catalog, 1:1 behavioral atomization, test commenting goals, file-splitting guidelines, and statement/branch coverage gates. Use whenever writing, reviewing, refactoring, or auditing pytest test suites or conftest.py files in any Python project.
---

# Python Testing Standards

Project-agnostic pytest conventions and quality goals for clean, deterministic, high-coverage Python test suites.

## When to Use

- Writing new `test_*.py` suites or updating existing tests.
- Organizing `conftest.py` fixtures or auditing fixture reuse and shadowing.
- Applying pytest markers, section banners, useful test comments, or splitting large test files.
- Enforcing statement and branch coverage gates.

## Core Standards

### 1. File Structure and Naming

- Mirror the source package layout under `tests/` (for example, `src/<pkg>/` -> `tests/test_<pkg>/`).
- Open every test file on Line 1 with a triple double-quoted module docstring declaring `Path: tests/...`, followed by `from __future__ import annotations`, grouped alphabetical imports, and `__version__`.
- Name test functions `test_<action>_<condition>_<expected_outcome>` with a single-line PEP 257 docstring starting with `"Verify..."`.
- Isolate and verify one user action, state mutation, or failure boundary per test function (1:1 behavioral atomization) without chaining unrelated actions.

### 2. Five-Marker Taxonomy

Decorate every test function with at least one registered marker (`--strict-markers`). Avoid obsolete markers (`burnin`, `slow`):

- `@pytest.mark.unit`: Pure in-memory logic with zero disk I/O, subprocess calls, or network calls.
- `@pytest.mark.regression`: Boundary conditions, invalid inputs, error branches, and bug-fix reproductions.
- `@pytest.mark.integration`: Multi-component workflows involving filesystem mutations, database persistence, serialization cycles, CLI pipelines, or backups.
- `@pytest.mark.integrity`: Whole-project schema constraints, directory topology checks, and enum parity invariants.
- `@pytest.mark.smoke`: High-level end-to-end gateway checks. Limit to 1 or 2 tests per file on primary entrypoints; avoid applying `smoke` to low-level helpers.

### 3. Fixtures, Sandboxing, and Execution

- Keep static fixtures under `tests/fixtures/<subject>/golden/` and `tests/fixtures/<subject>/failure/` using synthetic data only.
- Isolate filesystem mutations inside `tmp_path`.
- Run `pytest -v` directly when temporary directory routing is configured in `pyproject.toml`.
- Periodically audit `conftest.py` hierarchies to remove unused or unintentionally shadowed fixtures.

### 4. Coverage Quality Gates

Track both statement and branch coverage via `pytest-cov`:

- UI and presentation layers: >= 85.00%
- Core libraries and operational CLIs: >= 95.00%
- Developer automation and system utilities: 100.00%

## Organization and Style Goals (Flexible Guidelines)

The practices below are **goals and defaults**, not rigid rules. Apply them where they improve clarity and omit what does not fit a given module.

### 5. Predefined 6-Group Section Catalog

Organize tests using full-width ASCII comment banners rather than nested `class Test...` blocks. Use only the groups that apply to the module under test:

```python
# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Pure in-memory behavior and valid object construction.
# ==========================================================================
```

| Group | Default Marker | Typical Contents |
| :--- | :--- | :--- |
| **GROUP 1: Smoke & Primary Entrypoints** | `@pytest.mark.smoke` | 1-2 high-level end-to-end checks on the module's main entrypoint. |
| **GROUP 2: Core Logic & Happy Paths** | `@pytest.mark.unit` | Normal, expected in-memory behavior, valid object creation, and valid property-based (Hypothesis) cases. |
| **GROUP 3: Edge Cases & Boundary Conditions** | `@pytest.mark.regression` | Empty inputs, zero/max limits, tiebreakers, unusual valid values, and Hypothesis boundary/fuzzing cases. |
| **GROUP 4: Error Handling & Validation Failures** | `@pytest.mark.regression` | Invalid inputs, missing files, corrupted imports, permission errors, and expected exceptions or exit codes. |
| **GROUP 5: Filesystem, CLI & Integration** | `@pytest.mark.integration` | Disk reads/writes, database persistence, `tmp_path` sandboxes, Safe Backups, and CLI execution pipelines. |
| **GROUP 6: Integrity & Invariants** | `@pytest.mark.integrity` | Schema parity, directory topology checks, immutability, or workspace-wide invariants. |

- Classify single-line coverage tests and direct private-helper tests by **what behavior they verify** (usually Group 2, 3, or 4), rather than creating a separate "Coverage" or "Private" group.

### 6. Useful Test Commenting Goals

Aim for comments that explain **intent, setup, and invariants** rather than restating Python syntax:

- **Explain why mocks or tricky inputs exist:** Clarify the simulated condition (e.g., `# Simulate Windows file-locking collision during atomic replace`).
- **Explain boundary or magic values:** Note why a specific threshold or fixture value was chosen (e.g., `# Boundary: max_versions=5 triggers pruning on the 6th snapshot`).
- **Use `# Arrange` / `# Act` / `# Assert` on longer tests:** Helpful on multi-step or integration tests (~10+ lines) to keep setup, execution, and verification scannable.
- **Keep `# Note:` summaries on group banners:** State the behavioral contract covered by that section in one sentence.
- **Avoid source line-number references:** Describe the branch or defensive guard being verified (e.g., `# Fallback branch when config file is absent`) instead of brittle line numbers.

### 7. Splitting Long Test Files

- **Default:** Keep a single `test_<module>.py` for small and medium modules to avoid unnecessary file sprawl.
- **Goal for splitting:** When a test file grows past roughly 500-600 lines (or ~40+ tests), consider splitting it by group or focus area using `test_<module>_<group>.py` (for example, `test_backup_core.py`, `test_backup_errors.py`, `test_backup_integration.py`).
- Move fixtures shared across split test files into that directory's `conftest.py`.

## Gotchas

- When importing domain classes or enums whose names start with `Test*` (such as `TestimonyMedium`), set `[Class].__test__ = False` or alias the import so pytest does not collect them as test suites.