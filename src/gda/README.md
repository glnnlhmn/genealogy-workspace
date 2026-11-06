# Genealogy Digital Archive Engine (src/gda)

## Architectural Role
Top-level shared domain framework uniting core primitives, data models, entity resolvers, persistence engines, and archival utilities.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **`core/`**: GDA Core framework library.
- **`db/`**: Public package exports and facade for GDA persistence layer.
- **`engine/`**: Kinship graph analysis, plausibility engines, and relationship resolvers.
- **`entity/`**: Canonical entity representations and active archive registries.
- **`enums/`**: Authoritative controlled enumerations across the digital archive framework.
- **`io/`**: Genealogy Digital Archive I/O and persistence infrastructure.
- **`manager/`**: Stateful data access coordinators, vocabulary governors, and reference authorities.
- **`model/`**: Module stub for __init__.py.
- **`types/`**: Type definitions, enumerations, structural protocols, and classifications.
- **`util/`**: Stateless, pure helper utilities for strings, dates, paths, and phonetic hashing.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `src/system/gen_readme.py`.
