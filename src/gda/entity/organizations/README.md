<!--Path: src/gda/entity/organizations/README.md-->
# Voluntary & Institutional Organization Collection Manager (src/gda/entity/organizations)

## Architectural Role
Authoritative in-memory collection supporting standalone local chapters and parent/child hierarchies, multi-entity alias indexing, atomic child-reparenting retirement, and persistence gateway for Organization entities.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_entity/test_organizations/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `collection.py` | `1.0.0+build.4` | Authoritative in-memory collection and relational lookup manager for organization records. |
| `errors.py` | `1.0.0+build.1` | Domain-specific exception hierarchy for organization entity management. |
| `util.py` | `1.0.0+build.4` | Organization persistence, graveyard lifecycle operations, and serialization routines. |
| `validation.py` | `1.0.0+build.5` | Authoritative organization validation, URN pattern verification, and relational diagnostics. |

## Public Exports & Consumption Contract
Exports: `OrganizationError`, `OrganizationHierarchyError`, `OrganizationNotFoundError`, `OrganizationValidationError`, `Organizations`, `can_tombstone`, `can_undelete`, `export_file`, `import_file`, `load_from_db`, `save_to_db`, `tombstone_organization`, `undelete_organization`, `valid_collection_all`, `valid_collection_hierarchy`, `valid_collection_indexes`, `valid_collection_references`, `valid_collection_tombstones`, `valid_organization`, `valid_urn`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: bde0fc9adda000a8 -->
