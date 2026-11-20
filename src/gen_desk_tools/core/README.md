<!--Path: src/gen_desk_tools/core/README.md-->
# GenDesk Tools Core Primitives (gen_desk_tools.core)

## Architectural Role
Shared internal primitives for GenDesk Tools providing workspace root resolution, layered TOML configuration loading, atomic file writes and Safe Backup routing, logging setup, and common CLI argument helpers.

## Quality Gate & Verification Status
- **Quality Gate:** 100.00% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gen_desk_tools/test_core/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `backup.py` | `1.0.0+build.1` | Atomic file writes, protected-domain checks, and Safe Backup routing primitives. |
| `cli.py` | `1.0.0+build.1` | Shared CLI argument registration and interactive confirmation helpers for GDT. |
| `config.py` | `1.0.0+build.1` | Layered TOML configuration loader for GenDesk Tools (GDT). |
| `logging.py` | `1.0.0+build.1` | Standardized dual-handler UTF-8 logging setup for GenDesk Tools (GDT). |
| `workspace.py` | `1.0.0+build.1` | Workspace root discovery, POSIX path normalization, and root containment guards. |

## Public Exports & Consumption Contract
Exports: `DEFAULT_GDT_CONFIG`, `add_common_args`, `atomic_copy`, `atomic_write_text`, `create_safe_backup`, `deep_merge`, `ensure_within_root`, `is_protected_domain`, `load_gdt_config`, `prompt_yes_no`, `resolve_backup_dir`, `resolve_workspace_root`, `setup_tool_logger`, `to_posix_rel`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: c94be2027df943a0 -->
