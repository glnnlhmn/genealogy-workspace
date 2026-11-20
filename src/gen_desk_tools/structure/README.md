<!--Path: src/gen_desk_tools/structure/README.md-->
# GenDesk Structure Reporter (gd-struct)

## Architectural Role
Workspace directory tree and Git-aware file tree scanner generating depth-bounded structure reports into the configured reports directory.

## Quality Gate & Verification Status
- **Quality Gate:** 100.00% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gen_desk_tools/test_structure/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `cli.py` | `1.0.0+build.1` | Command-line interface entrypoint for GenDesk Structure (gd-struct). |
| `scanner.py` | `1.0.0+build.2` | Directory tree scanner and report generator for GenDesk Structure (gd-struct). |

## Public Exports & Consumption Contract
Exports: `DEFAULT_MAX_DEPTH`, `MANDATORY_EXCLUSIONS`, `MODE_TARGETS`, `build_git_tree`, `build_parser`, `build_tree`, `generate_structure_report`, `main`, `resolve_mode`, `run`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: e39405454e3aa202 -->
