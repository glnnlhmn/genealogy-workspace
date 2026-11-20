<!--Path: src/system/README.md-->
# Package Documentation (src/system)

## Architectural Role
Architectural subsystem package.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_system/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **`gd_metrics/`**: First-class code quality, coverage, and test suite telemetry package.
- **`gen_db/`**: Database provisioning and environment setup subsystem facade.
- **`gen_desk_mgr/`**: GenDesk Backup Manager facade package.
- **`gsi/`**: Genealogy Script Importer (GSI) package facade.
- **[hooks/](hooks/README.md)**: Subpackage domain entities and enumerations.
- **`util/`**: System utilities package facade.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `install_hooks.py` | `1.0.0+build.4` | Automated workstation onboarding and Git hook deployer. |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: f5f3c50caade75ee -->
