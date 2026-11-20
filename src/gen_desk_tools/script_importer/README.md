<!--Path: src/gen_desk_tools/script_importer/README.md-->
# GenDesk Script Importer (gsi)

## Architectural Role
Hermetic staging intake pipeline inspecting staged files for routing headers, enforcing Safe Backups on protected domains, relocating files, and optionally cleaning unparseable candidates.

## Quality Gate & Verification Status
- **Quality Gate:** 100.00% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gen_desk_tools/test_script_importer/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `cli.py` | `1.0.0+build.2` | Command-line interface entrypoint for GenDesk Script Importer (gsi). |
| `headers.py` | `1.0.0+build.4` | Multi-format routing header parser for GenDesk Script Importer (gsi). |
| `intake.py` | `1.0.0+build.3` | Hermetic file intake orchestrator for GenDesk Script Importer (gsi). |

## Public Exports & Consumption Contract
Exports: `build_parser`, `main`, `parse_metadata_header`, `run_intake`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 8305f09f2c54c4d7 -->
