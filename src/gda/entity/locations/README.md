# Jurisdictional Location Collection Manager & Hierarchy Graph (src/gda/entity/locations)

## Architectural Role
Authoritative in-memory collection, 5-tier Pattern 1-7 jurisdictional hierarchy builder, multi-hop cycle and root validator, atomic child-reparenting graveyard lifecycle, and persistence gateway for Location entities.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_entity/test_locations/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `collection.py` | `1.0.0+build.41` | Authoritative in-memory collection and relational graph manager for location records. |
| `errors.py` | `1.0.0+build.2` | Subsystem exception hierarchy for the locations domain entity library. |
| `util.py` | `1.0.0+build.46` | Authoritative jurisdictional hierarchy construction, graveyard lifecycle, and persistence. |
| `validation.py` | `1.0.0+build.24` | Authoritative jurisdictional URN, structural hierarchy, and path validation routines. |

## Public Exports & Consumption Contract
Exports: `LocationError`, `LocationHierarchyError`, `LocationNotFoundError`, `Locations`, `build_jurisdiction_hierarchy`, `can_tombstone`, `can_undelete`, `clean_string`, `export_file`, `import_file`, `load_from_db`, `save_to_db`, `slugify`, `tombstone_location`, `undelete_location`, `valid_collection_all`, `valid_collection_cycles`, `valid_collection_indexes`, `valid_collection_patterns`, `valid_collection_roots`, `valid_collection_tombstones`, `valid_display_text`, `valid_hierarchy`, `valid_urn`, `validate_urn_tier_sequence`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
