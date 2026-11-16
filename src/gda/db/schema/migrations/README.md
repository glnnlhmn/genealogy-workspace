# Modular Analytical SQLite DDL Migration Registry (src/gda/db/schema/migrations)

## Architectural Role
Versioned SQLite DDL migration scripts (v001_places through v005_indexes) provisioning flattened analytical entity tables, relational foreign keys, and B-Tree performance indexes.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_db/test_schema/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `v001_places.py` | `1.0.0+build.1` | Relational DDL migration defining core place entities (locations and sites). |
| `v002_organizations.py` | `1.0.0+build.1` | Relational DDL migration defining voluntary and institutional organizations. |
| `v003_personas.py` | `1.0.0+build.1` | Relational DDL migration defining individuals and domestic family units. |
| `v004_facts.py` | `1.0.0+build.1` | Relational DDL migration defining evidentiary fact assertions. |
| `v005_indexes.py` | `1.0.0+build.1` | Relational DDL migration establishing analytical B-Tree indexes for core entities. |

## Public Exports & Consumption Contract
Exports: `MIGRATION_REGISTRY`, `Migration`, `v001_places`, `v002_organizations`, `v003_personas`, `v004_facts`, `v005_indexes`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
