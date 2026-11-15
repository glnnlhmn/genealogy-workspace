# Evidentiary Fact Collection Manager & Timeline Index (src/gda/entity/facts)

## Architectural Role
Authoritative in-memory collection, secondary subject/type/location/site/participant indexing, outbound FK verification, graveyard lifecycle, and persistence gateway for Fact entities.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_entity/test_facts/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `collection.py` | `1.0.0+build.2` | Authoritative in-memory collection and relational lookup manager for evidentiary facts. |
| `errors.py` | `1.0.0+build.1` | Domain-specific exception hierarchy for evidentiary fact entity management. |
| `util.py` | `1.0.0+build.2` | Fact persistence, graveyard lifecycle operations, and serialization routines. |
| `validation.py` | `1.0.0+build.2` | Authoritative evidentiary fact validation, URN verification, and relational diagnostics. |

## Public Exports & Consumption Contract
Exports: `FactError`, `FactNotFoundError`, `FactValidationError`, `Facts`, `can_tombstone`, `can_undelete`, `export_file`, `import_file`, `load_from_db`, `save_to_db`, `tombstone_fact`, `undelete_fact`, `valid_collection_all`, `valid_collection_indexes`, `valid_collection_references`, `valid_collection_tombstones`, `valid_fact`, `valid_urn`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
