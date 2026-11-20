<!--Path: src/gen_desk_tools/readme_gen/README.md-->
# GenDesk README Generator (gdrm)

## Architectural Role
AST-driven package README.md generator with content hash verification, scope/alias package resolution, and overwrite protection.

## Quality Gate & Verification Status
- **Quality Gate:** 100.00% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gen_desk_tools/test_readme_gen/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `cli.py` | `1.0.0+build.2` | Command-line interface entrypoint for GenDesk README Generator (gdrm). |
| `generator.py` | `1.0.0+build.2` | Package README.md rendering, scope filtering, hash protection, and execution engine. |
| `parser.py` | `1.0.0+build.1` | AST-driven metadata extraction for Python source modules. |

## Public Exports & Consumption Contract
Exports: `DEFAULT_PACKAGES_REL_PATH`, `SCOPE_ALIASES`, `build_parser`, `compute_content_hash`, `extract_module_metadata`, `generate_package_readme`, `is_unmodified_generated_readme`, `load_package_definitions`, `main`, `prompt_overwrite`, `resolve_target_packages`, `run`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 90fad69f7f473e52 -->
