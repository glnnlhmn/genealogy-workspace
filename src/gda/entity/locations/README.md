# Package Documentation (src/gda/entity/locations)

## Architectural Role
Architectural subsystem package.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_locations/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `collection.py` | `1.0.0+build.36` | Authoritative in-memory collection and relational graph manager for location records. |
| `errors.py` | `1.0.0+build.2` | Subsystem exception hierarchy for the locations domain entity library. |
| `util.py` | `1.0.0+build.39` | Authoritative jurisdictional hierarchy construction, graveyard lifecycle, and persistence. |
| `validation.py` | `1.0.0+build.16` | Authoritative jurisdictional URN, structural hierarchy, and path validation routines. |

## Public Exports & Consumption Contract
Exports: `LocationError`, `LocationHierarchyError`, `LocationNotFoundError`, `Locations`, `clean_string`, `export_file`, `import_file`, `load_from_db`, `save_to_db`, `slugify`, `valid_collection_all`, `valid_collection_cycles`, `valid_collection_indexes`, `valid_collection_patterns`, `valid_collection_roots`, `valid_collection_tombstones`, `valid_display_text`, `valid_hierarchy`, `valid_urn`.

---
Generated dynamically by `src/system/gen_readme.py`.
