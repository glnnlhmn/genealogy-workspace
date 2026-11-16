# Schema Migration Coordinator & DDL Engine (src/gda/db/schema)

## Architectural Role
Governs SQLite schema version discovery, idempotent migration execution, and atomic DDL bootstrap via SchemaManager.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_db/test_schema/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[migrations/](migrations/README.md)**: Migration registry and automated script discovery for GDA DB schema.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `manager.py` | `1.0.0+build.5` | Schema migration engine and DDL execution coordinator for GDA DB. |

## Public Exports & Consumption Contract
Exports: `MIGRATION_REGISTRY`, `Migration`, `SchemaManager`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
