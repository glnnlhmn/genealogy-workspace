<!--Path: src/gen_desk_tools/metrics/README.md-->
# GenDesk Telemetry & Metrics Pipeline (gd-metrics)

## Architectural Role
Multi-stage code quality, coverage, test suite AST analysis, module hygiene, import boundary, mypy, and Ruff telemetry pipeline with local JSON and Google Sheets exporters.

## Quality Gate & Verification Status
- **Quality Gate:** 100.00% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gen_desk_tools/test_metrics/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[collectors/](collectors/README.md)**: Telemetry collectors for Radon, pytest coverage, AST analysis, mypy, and Ruff.
- **[exporters/](exporters/README.md)**: Telemetry exporters for Google Sheets sync and local JSON snapshots.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `cli.py` | `1.0.0+build.3` | Command-line interface and 7-stage pipeline orchestrator for gd_metrics. |
| `config.py` | `1.0.0+build.2` | Four-layer configuration loader for gd_metrics. |
| `progress.py` | `1.0.0+build.2` | Real-time stage and file progress reporter for gd_metrics. |

## Public Exports & Consumption Contract
Exports: `BatchDefinition`, `MetricsConfig`, `ProgressReporter`, `__version__`, `load_config`, `resolve_batches`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: eba2cbab8caa5e4c -->
