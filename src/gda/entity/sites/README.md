# Physical Site Collection Manager & Spatial Lookup Index (src/gda/entity/sites)

## Architectural Role
Authoritative in-memory collection, governing LocationID and SiteType bucket indexing, multi-entity alias lookup, graveyard lifecycle, and persistence gateway for physical Site entities.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_entity/test_sites/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `collection.py` | `1.0.0+build.7` | Authoritative in-memory collection and relational lookup manager for site records. |
| `errors.py` | `1.0.0+build.1` | Subsystem exception hierarchy for the sites domain entity library. |
| `util.py` | `1.0.0+build.15` | Site persistence, graveyard lifecycle operations, and serialization routines. |
| `validation.py` | `1.0.0+build.8` | Authoritative site validation, URN pattern verification, and relational diagnostics. |

## Public Exports & Consumption Contract
Exports: `SiteError`, `SiteNotFoundError`, `SiteValidationError`, `Sites`, `can_tombstone`, `can_undelete`, `export_file`, `import_file`, `load_from_db`, `save_to_db`, `tombstone_site`, `undelete_site`, `valid_collection_all`, `valid_collection_indexes`, `valid_collection_locations`, `valid_collection_tombstones`, `valid_site`, `valid_site_address`, `valid_urn`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
