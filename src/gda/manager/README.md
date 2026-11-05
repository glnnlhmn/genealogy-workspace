# Governance & Reference Minting Managers (src/gda/manager)

## Architectural Role
High-level authority management coordinators overseeing global vocabulary registries, namespace dereferencing, and identifier minting.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **`referencer/`**: Canonical URN minting, URI resolution, and colloquial geographic mapping.
- **`vocab/`**: Controlled vocabulary token governance, taxonomy indexing, and drift detection.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `src/system/gen_readme.py`.
