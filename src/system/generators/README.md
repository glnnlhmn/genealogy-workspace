# Synthetic Data & Fixture Generators (src/system/generators)

## Architectural Role
Synthetic fixture generation, geographical location test data synthesis, and testing harness mock builders.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_system/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `create_location_fixtures.py` | `1.0.0+build.1` | Automated generator for location intake golden and failure test fixtures. |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `src/system/gen_readme.py`.
