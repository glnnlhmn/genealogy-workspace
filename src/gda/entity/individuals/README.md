<!--Path: src/gda/entity/individuals/README.md-->
# Individual Persona Collection Manager & Onomastic Index (src/gda/entity/individuals)

## Architectural Role
Authoritative in-memory collection, birth/married surname and multi-entity alias indexing, vital place FK verification, graveyard lifecycle, and persistence gateway for Individual entities.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_entity/test_individuals/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `collection.py` | `1.0.0+build.4` | Authoritative in-memory collection and relational lookup manager for individuals. |
| `errors.py` | `1.0.0+build.1` | Domain-specific exception hierarchy for individual persona entity management. |
| `util.py` | `1.0.0+build.3` | Individual persistence, graveyard lifecycle operations, and serialization routines. |
| `validation.py` | `1.0.0+build.3` | Authoritative individual validation, URN verification, and relational diagnostics. |

## Public Exports & Consumption Contract
Exports: `IndividualError`, `IndividualNotFoundError`, `IndividualValidationError`, `Individuals`, `can_tombstone`, `can_undelete`, `export_file`, `import_file`, `load_from_db`, `save_to_db`, `tombstone_individual`, `undelete_individual`, `valid_collection_all`, `valid_collection_indexes`, `valid_collection_references`, `valid_collection_tombstones`, `valid_individual`, `valid_urn`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 76d2220f6901d6d4 -->
