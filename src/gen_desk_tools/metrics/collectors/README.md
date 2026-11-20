<!--Path: src/gen_desk_tools/metrics/collectors/README.md-->
# GenDesk Metrics Collectors (gen_desk_tools.metrics.collectors)

## Architectural Role
Telemetry collectors for Radon raw/complexity/maintainability metrics, pytest-cov statement and branch coverage, AST conftest and marker analysis, module hygiene, import dependency graphs, mypy diagnostics, and Ruff lint findings.

## Quality Gate & Verification Status
- **Quality Gate:** 100.00% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gen_desk_tools/test_metrics/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `coverage_collector.py` | `1.0.0+build.3` | Pytest branch and statement coverage collector for gd_metrics. |
| `hygiene_collector.py` | `1.0.0+build.5` | AST-based module hygiene collector for header, PEP 440 version, and test parity checks. |
| `import_collector.py` | `1.0.0+build.4` | AST-based import dependency graph and architectural boundary violation collector. |
| `mypy_collector.py` | `1.0.0+build.4` | Subprocess collector for mypy static type-check diagnostics. |
| `pytest_analyzer.py` | `1.0.0+build.6` | AST-based pytest suite analyzer for conftest mapping, fixture reuse, and markers. |
| `radon_collector.py` | `1.0.0+build.4` | Radon static metrics collector (raw, cyclomatic complexity, maintainability). |
| `ruff_collector.py` | `1.0.0+build.3` | Subprocess collector for Ruff JSON lint diagnostics. |

## Public Exports & Consumption Contract
Exports: `BatchRadonRollup`, `ComplexityHotspot`, `ConftestFixtureRecord`, `CoverageRunResult`, `FileCoverageMetrics`, `FileMarkerSummary`, `FileRadonMetrics`, `ImportEdgeRecord`, `ModuleHygieneRecord`, `MypyDiagnostic`, `MypyRunResult`, `PytestSuiteAnalysis`, `RuffDiagnostic`, `RuffRunResult`, `__version__`, `analyze_file_radon`, `analyze_pytest_suite`, `collect_hygiene_metrics`, `collect_import_graph`, `collect_radon_metrics`, `discover_batch_files`, `format_missing_lines`, `parse_coverage_json`, `parse_mypy_output`, `parse_ruff_json`, `run_mypy_check`, `run_pytest_coverage`, `run_ruff_check`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 68631a9426ae4734 -->
