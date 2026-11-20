<!--Path: src/gda/db/schema/migrations/README.md-->
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
| `v006_sources_vital_cemetery.py` | `1.0.0+build.1` | Migration v006: Archival source tables and indexes for Vital and Cemetery domains. |
| `v007_sources_enumerated_publications.py` | `1.0.0+build.1` | Migration v007: Archival source tables and indexes for Enumerated and Publications domains. |
| `v008_sources_probate_land.py` | `1.0.0+build.1` | Migration v008: Archival source tables and indexes for Probate and Land domains. |
| `v009_sources_immigration_military.py` | `1.0.0+build.1` | Migration v009: Archival source tables and indexes for Immigration and Military domains. |
| `v010_sources_education_manuscripts_orgs_other.py` | `1.0.0+build.1` | Migration v010: Archival source tables and indexes for Education, Manuscripts, |
| `v011_xrefs.py` | `1.0.0+build.1` | Migration v011: Cross-reference bridge and derived index tables (gda.model.xref). |

## Public Exports & Consumption Contract
Exports: `MIGRATION_REGISTRY`, `Migration`, `v001_places`, `v002_organizations`, `v003_personas`, `v004_facts`, `v005_indexes`, `v006_sources_vital_cemetery`, `v007_sources_enumerated_publications`, `v008_sources_probate_land`, `v009_sources_immigration_military`, `v010_sources_education_manuscripts_orgs_other`, `v011_xrefs`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 02674e0c41930207 -->
