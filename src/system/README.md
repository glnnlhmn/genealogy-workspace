# System Administration & Automation (src/system)

## Architectural Role
Workstation administration, developer environment onboarding, Git hook deployment, and automated intake pipelines.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_system/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `check_structure.py` | `0.0.1+build.r4` | Directory tree inspection utility for workspace auditing and reporting. |
| `generate_readmes.py` | `1.0.0+build.1` | Dynamic package documentation generator for completed GDA framework modules. |
| `gsi.py` | `1.4.0+build.r3` | Genealogy Script Importer (GSI). |
| `install_hooks.py` | `1.0.0+build.r2` | Genealogy Workspace Git Hooks Installer. |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `src/system/generate_readmes.py`.
