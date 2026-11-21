<!--Path: src/gen_desk_tools/radon_report/README.md-->
# GenDesk Radon Report (gdradon)

## Architectural Role
Combined Radon cyclomatic complexity (CC), maintainability index (MI), and raw line metrics report generator.

## Quality Gate & Verification Status
- **Quality Gate:** 100.00% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gen_desk_tools/test_radon_report/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `cli.py` | `1.0.0+build.2` | Command-line interface entrypoint for GenDesk Radon Report (gdradon). |
| `scanner.py` | `1.0.0+build.2` | Combined Radon static analysis report generator (CC, MI, and RAW) for GenDesk Tools. |

## Public Exports & Consumption Contract
Exports: `DEFAULT_MAX_DEPTH`, `MODE_TARGETS`, `__version__`, `build_combined_radon_report`, `build_parser`, `format_radon_section`, `generate_radon_report`, `main`, `run`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 0055d3e5e9e05096 -->
