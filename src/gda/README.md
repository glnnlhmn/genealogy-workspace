<!--Path: src/gda/README.md-->
# Genealogy Digital Archive Framework (src/gda)

## Architectural Role
Top-level shared domain framework uniting core primitives, controlled enumerations, atomic/Safe-Backup I/O, helper utilities, the five-pillar domain model suite, in-memory domain entity collection managers, and the SQLite analytical database layer.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[core/](core/README.md)**: Core infrastructure, configuration, error contracts, and runtime introspection.
- **[db/](db/README.md)**: Database persistence, schema migration, and entity mapping facade for GDA.
- **[engine/](engine/README.md)**: Kinship graph analysis, plausibility engines, and relationship resolvers.
- **[entity/](entity/README.md)**: Domain entity collection managers, validation services, and persistence gateways.
- **[io/](io/README.md)**: Genealogy Digital Archive I/O and persistence infrastructure.
- **[manager/](manager/README.md)**: Stateful data access coordinators, vocabulary governors, and reference authorities.
- **[model/](model/README.md)**: Authoritative five-pillar domain model suite for the Genealogy Digital Archive.
- **`repository/`**: Unified persistence, query, and in-memory collection layer for GDA.
- **[util/](util/README.md)**: Stateless utility functions for identifier management and text processing.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Exports: `core`, `db`, `entity`, `io`, `model`, `util`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 3a3dc46a6825c83b -->
