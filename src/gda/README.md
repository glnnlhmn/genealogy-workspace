# Genealogy Digital Archive Framework (src/gda)

## Architectural Role
Top-level shared domain framework uniting core primitives, controlled enumerations, atomic/Safe-Backup I/O, helper utilities, and the five-pillar domain model suite.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[core/](core/README.md)**: Core infrastructure, configuration, error contracts, and runtime introspection.
- **[db/](db/README.md)**: Public package exports and facade for GDA persistence layer.
- **[engine/](engine/README.md)**: Kinship graph analysis, plausibility engines, and relationship resolvers.
- **[entity/](entity/README.md)**: Canonical entity representations and active archive registries.
- **[io/](io/README.md)**: Genealogy Digital Archive I/O and persistence infrastructure.
- **[manager/](manager/README.md)**: Stateful data access coordinators, vocabulary governors, and reference authorities.
- **[model/](model/README.md)**: Authoritative five-pillar domain model suite for the Genealogy Digital Archive.
- **`repository/`**: Persistence repository interfaces and implementations for GDA models.
- **[util/](util/README.md)**: Domain-specific helper utilities for identifiers, text sanitization, and phonetics.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
