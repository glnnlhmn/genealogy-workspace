---
# Path: .skills/test-suite-audit/SKILL.md
name: test-suite-audit
description: Conduct a dedicated Ground-Up Test Suite, Coverage, Marker, and conftest.py Fixture Hierarchy Audit across tests/, producing an executive summary in chat and a 5-tab live Google Sheet tracker in Google Drive.
---

# GDA Test Suite & Fixture Architecture Audit

Conduct an independent, ground-up audit of the GDA test harness (`tests/test_gda/`, `tests/test_system/`, and `conftest.py` files) decoupled from production code refactoring. Evaluate 1:1 module mirroring, statement and branch coverage, `conftest.py` fixture deduplication, marker discipline, assertion rigor, and Windows/Google Drive I/O safety.

Deliver a concise **Test Suite Summary** in chat and create a **5-tab live Google Sheet** directly in Google Drive to plan and track test suite improvements.

## When to Use

- The user asks to audit, review, or consolidate the test suite (`tests/`), `conftest.py` fixture hierarchy, test coverage, or test markers.
- After completing a production refactoring phase to ensure test hygiene, eliminate duplicated helper builders across test files, and verify 100% statement and branch coverage.

## Workspace Directory Conventions

- **Canonical Workspace Root**: `G:/My Drive/genealogy-workspace`
- **Pytest Basetemp**: `C:/temp/pytest_tmp` (configured in `pyproject.toml` to prevent Google Drive file locking).
- **Workspace Scratch Directory**: Always use `gtemp/` (never `temp/`).
- **Staging Directory**: `download/` (ingested via `gsi`).
- **Reports Directory**: `reports/` (houses `gd_code_scoring_report.txt` and coverage gap reports).

## 7 Test Audit Dimensions

Evaluate the target test directories across all 7 dimensions and assign deterministic Audit IDs (`TST-1`, `TST-2`, ...):

1. **1:1 Module Mirroring & Orphaned Test Detection**:
   - Verify every production module `src/<pkg>/<module>.py` has a corresponding `tests/test_<pkg>/test_<module>.py` (or domain sub-suite).
   - Flag orphaned test files whose corresponding production module was moved, renamed, or deleted.
2. **Tiered `conftest.py` Fixture Architecture (DRY)**:
   - Identify duplicated private helper builders (`_now()`, `_audit()`, sample `Location`/`Site`/`Individual`/`Family`/`Fact`/`SourceRecord` factories, and SQLite session fixtures) repeated across multiple `test_*.py` files.
   - Plan hoisting into the appropriate `conftest.py` tier (`tests/conftest.py` for global atoms/audits/sessions vs. package-level `conftest.py` for domain entities/sources).
3. **Statement & Branch Coverage Completeness**:
   - Require 100% statement and branch coverage across target packages (`pytest --cov --cov-branch --cov-report=term-missing`).
   - Use `extract-coverage-gaps` (`src/system/util/extract_coverage_gaps.py`) when missing lines or partial branches exist.
4. **Pytest Marker Hygiene (`@pytest.mark.*`)**:
   - Verify every test function is decorated with one of the strict markers registered in `pyproject.toml`: `@pytest.mark.unit`, `@pytest.mark.regression`, `@pytest.mark.integration`, `@pytest.mark.smoke`, or `@pytest.mark.integrity`.
5. **Assertion Depth & Boundary Rigor**:
   - Ensure tests verify true domain invariants and boundary edge cases rather than superficial line execution:
     - `bool`-as-`int` rejection (`True`/`False` passed to `int`/`float` fields).
     - Whitespace-only strings, leading/trailing whitespace normalization, and case-insensitive enum coercion.
     - Malformed SmartIDs and UUIDs returning `False`/`None`/`[]` on collection lookups (`__contains__`, `get`, `get_any`).
     - Tombstone retirement, cycle guards in `resolve_active()`, and active-child reparenting.
     - Lossless `to_dict`/`from_dict`, `to_json`/`from_json`, and `to_row`/`from_row` round-trips.
     - Custom dunder protocols (`__eq__`, `__hash__`, `__lt__`, `__str__`, `__repr__`).
6. **Test Isolation & Windows / Google Drive I/O Safety**:
   - Verify `@pytest.mark.unit` tests execute purely in memory with zero disk or SQLite file I/O (or use `:memory:` / mocked persistence).
   - Verify filesystem integration tests use `tmp_path` and never reopen an open `NamedTemporaryFile` handle on Windows.
7. **Test Code Quality, Typing & Radon Metrics**:
   - Verify test files carry `Path: tests/...` docstring headers, `__version__`, full type annotations (`mypy tests`), Ruff compliance, and clean Cyclomatic Complexity / Maintainability Index scores in `gd_code_scoring_report.txt`.

## Deliverable Format: Live 5-Tab Google Sheet + Chat Summary

### 1. Create the Live 5-Tab Google Sheet in Google Drive

Use `drive:create_file` (with `mime_type="application/vnd.google-apps.spreadsheet"`) followed by `sheets_agent:call` to create and populate a formatted 5-tab Google Sheet titled `GDA Test Suite Audit - <Scope> (<YYYY-MM-DD>)`:

- **Tab 1: `Test_Scorecard`**
  - Columns: `Test Domain | Test Files | Source Files | Mirror Parity % | Test SLOC | Test:Src SLOC Ratio | Doc % | Stmt Coverage % | Branch Coverage % | Avg CC | MI Grade A % | Ruff/Mypy Status | Verdict`
- **Tab 2: `Test_Mirror_Inventory`**
  - Columns: `Package | Source File Path | Corresponding Test File(s) | Stmt Cov % | Branch Cov % | Missing Lines/Branches | Markers Present | Mirror Status (Matched / Missing Test / Orphaned Test)`
- **Tab 3: `Fixture_&_Conftest_Plan`**
  - Columns: `Fixture / Helper Name | Currently Duplicated In (Test Files) | Target conftest.py Path | Fixture Scope (function/module/session) | Est. SLOC Saved | Assigned Batch`
- **Tab 4: `Test_Quality_Findings`**
  - Columns: `Finding ID (TST-1..) | Severity (High/Medium/Low) | Category (Coverage/Fixture-DRY/Markers/Boundary-Rigor/Isolation/Style) | Test File Path | Test Function / Lines | Observation | Proposed Remediation | Assigned Batch | Status`
- **Tab 5: `Test_Batch_Plan`**
  - Columns: `Stage | Batch ID | Target Test / conftest.py Files (4-8 max) | Finding IDs Resolved | Verification Gate (gsi, rfmt, pytest --cov-branch, mypy) | Status`

### 2. Concise Chat Summary

Provide a brief summary in chat highlighting coverage health, top `conftest.py` deduplication opportunities, and any decision points before generating test batches.

## Guardrails

- **Hold on Unapproved Test Code Generation**: Do NOT generate refactored test files during the audit turn. Wait for user approval of the batch plan.
- **Sub-Batch Size Limit**: Limit each test generation batch to 4 to 8 files maximum.
- **No Em-Dashes or En-Dashes**: Use hyphens or colons in prose and spreadsheet cells.