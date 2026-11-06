# Database Relational DDL & Migrations (src/gda/db/schema)

## Architectural Role
Versioned SQLite schema migration runners, table definitions, index initializers, and schema lifecycle managers.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_db/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **`migrations/`**: Migration registry and automated script discovery for GDA DB schema.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `manager.py` | `1.0.0+build.4` | Schema migration engine and DDL execution coordinator for GDA DB. |

## Public Exports & Consumption Contract
Exports: `MIGRATION_REGISTRY`, `Migration`, `SchemaManager`.

---
Generated dynamically by `src/system/gen_readme.py`.
