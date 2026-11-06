# Authoritative Domain Model Suite (src/gda/model)

## Architectural Role
Central structural data model hierarchy defining atomic primitives, composite base structures, primary entities, and relational edges.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **`atom/`**: Atomic identification, temporal, metric, and spatial primitives package.
- **`base/`**: Base model value objects, audit envelopes, and tombstoning contracts.
- **`entity/`**: Authoritative domain entity dataclass definitions extending BaseEntity.
- **`enumerated/`**: Enumerated classification models and taxonomy wrappers.
- **`media/`**: Digital media, artifact metadata, and citation binding models.
- **`military/`**: Military evidentiary domain models partitioned by record classification.
- **`orgs/`**: Institutional, religious, military, and civil organization models.
- **`vital/`**: Vital event record definitions.
- **`xref/`**: Cross-reference and relational edge models for the genealogical digital archive.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `src/system/gen_readme.py`.
