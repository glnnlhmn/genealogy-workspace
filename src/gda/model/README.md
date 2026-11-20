<!--Path: src/gda/model/README.md-->
# Authoritative Domain Model Suite (src/gda/model)

## Architectural Role
Five-pillar structural data model hierarchy uniting atomic primitives (atom), composite base structures (base), canonical graph entities (entity), documentary source records (source), and derived cross-reference edges (xref).

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[atom/](atom/README.md)**: Atomic identification, temporal, metric, and spatial primitives package.
- **[base/](base/README.md)**: Foundational composite value objects, entity envelopes, and lifecycle mixins.
- **[entity/](entity/README.md)**: Authoritative domain entity dataclass definitions extending BaseEntity.
- **[source/](source/README.md)**: Archival documentary source record models across all historical domains.
- **[xref/](xref/README.md)**: Cross-reference bridge and derived index models for the GDA domain layer.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Exports: `atom`, `base`, `entity`, `source`, `xref`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 61564e8d14997f5b -->
