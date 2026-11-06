<!--Path: prompts/topics/topic_test_harness.md-->
# Topic Specification: Test Suite Architecture, Markers & Protocols

## 1. Scope & Packaging Governance
This specification governs test architecture, execution isolation, marker semantics, fixture management, and quality gates across the digital archive.
* **Packaging Configuration:** Governed by the workspace root pyproject.toml (PEP 518/621).
* **Test Suite Placement:** Test suites reside under tests/, partitioned by subsystem:
  * tests/test_gda/: Core library, I/O, schema, and domain tests (targeting src/gda/).
  * tests/test_cli/: Operational CLI tool tests (targeting src/cli/).
  * tests/test_system/: System administration and workstation automation tests (targeting src/system/).
  * tests/test_ancestry_desk/: Desktop presentation layer tests (targeting src/ancestry_desk/).

## 2. Test File Header & Structural Organization

### 2.1 File-Level Metadata Header & Docstring
Every test file strictly adheres to the Single-Field Header & Docstring Architecture. The file must open on Line 1 with the opening triple double-quote of the module docstring containing Path: tests/... . Top-level comment headers (# Name:, # Path:) are strictly prohibited to comply with PEP 257 and prevent Ruff D100 and E402 linting errors.

Compiler directives (from __future__ import annotations) immediately follow the closing docstring, followed by grouped alphabetical imports and __version__:

```python
"""Path: tests/test_system/test_gsi.py

One-line summary of test suite scope and target component.

"""

from __future__ import annotations

import pytest

from system.gsi import import_script

__version__ = "1.0.0+build.1"
```

### 2.2 Functional Group Section Dividers
Test files organize related test functions using standardized full-width ASCII comment banners rather than nested test classes:

```python
# ==========================================================================
# GROUP [N]: [Functional Category Title]
# Note: [Brief summary of invariants, behaviors, and boundaries tested]
# ==========================================================================
```

### 2.3 Test Function Conventions
* **Naming Syntax:** test_<method_or_action>_<condition_or_scenario>_<expected_outcome>
* **Function Docstrings:** Concise, single-line PEP 257 docstring starting with the imperative verb "Verify...".
* **Clean Bodies:** No metadata blocks or header boxes within test functions.

## 3. Behavioral Contract Atomization (1:1 Principle)
* **Single Behavioral Action:** Isolate and verify exactly one user action, state mutation, or failure boundary per test function.
* **Cohesive Assertion Boundaries:** Testing the immediate, natural consequences of a single action within one function is standard practice.
* **No Unrelated Action Chaining:** Testing independent actions sequentially within a single test function is strictly prohibited.

## 4. Pytest Marker Taxonomy & Tier Distribution
Every test function must be decorated with at least one registered pytest marker (`--strict-markers` enforced). Unregistered or obsolete markers (`burnin`, `slow`) are strictly prohibited and removed from configuration.

### 4.1 Registered Markers
* `@pytest.mark.unit`: Isolated standalone component, function, or class tests executing entirely in memory with zero production disk I/O, subprocess execution, or external network calls.
* `@pytest.mark.regression`: Boundary, defect reproduction, validation failure, edge case, and tiebreaker tests verifying defensive constraints and regressions.
* `@pytest.mark.integration`: Multi-component tests involving filesystem mutations, serialization/deserialization cycles, CLI execution pipelines, GSI staging, or Safe Backup creation.
* `@pytest.mark.integrity`: Whole-archive schema constraints, directory topology synchronization, enum parity invariants, and manifest drift checks.
* `@pytest.mark.smoke`: High-level end-to-end execution path checks validating primary happy paths and critical subsystem entrypoints.

### 4.2 Marker Allocation & Smoke Reduction Heuristics
To prevent marker inflation and preserve the fast diagnostic utility of test runs, test suites must adhere to the following distribution rules:
* **Reserve `@pytest.mark.smoke` for Subsystem Gateways:** Restrict `smoke` strictly to the primary entrypoint of a module or tool (typically 1 to 2 tests per file verifying end-to-end execution). Low-level primitives, atomic helper methods, validation boundaries, and utility functions must **never** be decorated with `smoke`.
* **Prioritize `@pytest.mark.unit` for Pure Logic:** In-memory value objects, enum parsing, string formatting, date normalization, and introspectable mixins belong strictly under `unit`.
* **Direct Defensive Edge Cases to `@pytest.mark.regression`:** Error handling branches, invalid input rejections, regex boundary mismatches, and bug-fix reproductions must be tagged as `regression`.
* **Isolate Disk and Subsystem Contracts with `@pytest.mark.integration`:** File writes, directory scans, atomic staging runs, and cross-package orchestrations must be marked as `integration`.

## 5. Fixture Hierarchy, Sandboxing & Privacy Rules
* **Static Fixture Hierarchy:** Shared baselines reside under tests/fixtures/[subject]/golden/ and tests/fixtures/[subject]/failure/.
* **Synthetic Privacy:** All fixtures use strictly handcrafted, synthetic data. No real living persons or private records.
* **Hermetic Sandboxing:** Production mutations execute within isolated temporary sandboxes (tmp_path).
* **Windows Sandbox Path:** Standard pytest invocations isolate temporary storage:
  ```bash
  pytest <target> -v --basetemp=gtemp/pytest_tmp
  ```

## 6. Coverage Quality Gates
Coverage quality gates are strictly tracked via pytest-cov across statement and branch coverage. While the overarching architectural target for all production modules is 100.00%, minimum enforcement gates are partitioned by subsystem criticality:

* **Desktop Application & UI Views (`src/ancestry_desk/`):** Baseline threshold **>= 85.00%** statement and branch coverage[cite: 1].
* **Core Framework Libraries & Operational CLI (`src/gda/`, `src/cli/`):** Minimum threshold **>= 95.00%** statement and branch coverage[cite: 1].
* **Workstation & System Utilities (`src/system/`):** Strict threshold **100.00%** statement and branch coverage[cite: 1].

## 7. Native Delivery & GSI Intake
Test files are delivered directly as pure .py files. GSI extracts the destination path from the in-docstring Path: declaration, creates pre-execution Safe Backups in archive/backups_[project]/, relocates files to their canonical destinations, and triggers verification.
