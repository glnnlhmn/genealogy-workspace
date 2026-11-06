# Domain Entity Services (src/gda/entity)

## Architectural Role
Operational domain entity lifecycle controllers, entity registry aggregation, and validation coordinators.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_entity/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **`locations/`**: Locations domain entity package exposing collection, utility, and validation entry points.
- **`sites/`**: Authoritative physical site entity management subpackage.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `src/system/gen_readme.py`.
