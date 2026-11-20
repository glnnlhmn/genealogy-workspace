<!--Path: src/gda/entity/families/README.md-->
# Domestic Family Unit Collection Manager & Kinship Index (src/gda/entity/families)

## Architectural Role
Authoritative in-memory collection, spousal partner and filial child indexing, union classification queries, graveyard lifecycle, and persistence gateway for Family entities.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_entity/test_families/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `collection.py` | `1.0.0+build.4` | Authoritative in-memory collection and relational lookup manager for family units. |
| `errors.py` | `1.0.0+build.1` | Domain-specific exception hierarchy for domestic family unit management. |
| `util.py` | `1.0.0+build.3` | Family persistence, graveyard lifecycle operations, and serialization routines. |
| `validation.py` | `1.0.0+build.2` | Authoritative family validation, URN verification, and relational diagnostics. |

## Public Exports & Consumption Contract
Exports: `Families`, `FamilyError`, `FamilyNotFoundError`, `FamilyValidationError`, `can_tombstone`, `can_undelete`, `export_file`, `import_file`, `load_from_db`, `save_to_db`, `tombstone_family`, `undelete_family`, `valid_collection_all`, `valid_collection_indexes`, `valid_collection_references`, `valid_collection_tombstones`, `valid_family`, `valid_urn`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: e2d077169bcabd93 -->
