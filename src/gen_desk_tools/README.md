<!--Path: src/gen_desk_tools/README.md-->
# GenDesk Tools Namespace Package (gen_desk_tools)

## Architectural Role
Top-level namespace and workstation tooling root providing shared core primitives, backup management, coverage gap extraction, telemetry collection, combined Radon reporting, README generation, script intake, and directory structure reporting.

## Quality Gate & Verification Status
- **Quality Gate:** 100.00% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gen_desk_tools/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[backup_mgr/](backup_mgr/README.md)**: GenDesk Backup Manager package (gdb).
- **[core/](core/README.md)**: Shared internal primitives for GenDesk Tools (workspace, config, backup, logging, CLI, process).
- **[coverage_gaps/](coverage_gaps/README.md)**: GenDesk Coverage Gaps package (gaps).
- **[metrics/](metrics/README.md)**: First-class code quality, coverage, and test suite telemetry package.
- **`radon_report/`**: Combined Radon static analysis report package (gdradon).
- **[readme_gen/](readme_gen/README.md)**: AST-driven package README.md documentation generator package (gdrm).
- **[script_importer/](script_importer/README.md)**: Hermetic script and asset intake pipeline package (gsi).
- **[structure/](structure/README.md)**: GenDesk Structure package (gd-struct).

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 9e5168b51104c838 -->
