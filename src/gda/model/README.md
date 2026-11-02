# Package Documentation (src/gda/model)

## Architectural Role
Architectural subsystem package.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_model/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **`atom/`**: Atomic identification, temporal, metric, and spatial primitives package.
- **`base/`**: Base model value objects, audit envelopes, and tombstoning contracts.
- **`entity/`**: Authoritative domain entity dataclass definitions extending BaseEntity.
- **`enumerated/`**: Enumerated records covering census listings, tax assessments, and directories.
- **`media/`**: Digital asset metadata, transcript bindings, and MIME classification models.
- **`military/`**: Military evidentiary domain models partitioned by record classification.
- **`orgs/`**: Organizational structures, religious bodies, fraternities, and institutions.
- **`vital/`**: Vital event models covering birth, marriage, divorce, death, and burial.
- **`xref/`**: Cross-reference and relational edge models for the genealogical digital archive.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `src/system/gen_readme.py`.
