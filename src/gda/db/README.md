# Embedded Relational Persistence & Schema Management (src/gda/db)

## Architectural Role
Embedded SQLite relational persistence layer providing connection lifecycle management, WAL and foreign key enforcement, atomic write transactions, versioned DDL schema migrations, and bidirectional Pydantic row mapping.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_db/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **`schema/`**: Schema management facade for GDA persistence layer.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `exceptions.py` | `1.0.0+build.1` | Database exception hierarchy and error translation contracts for GDA DB. |
| `mapper.py` | `1.0.0+build.12` | Bidirectional relational row-to-model mappers bridging SQLite and Pydantic entities. |
| `session.py` | `1.0.0+build.5` | Connection lifecycle, transaction orchestration, and PRAGMA management for GDA DB. |

## Public Exports & Consumption Contract
Exports: `BaseRowMapper`, `ConnectionTimeoutError`, `ConstraintViolationError`, `DatabaseConfig`, `DatabaseConnectionError`, `DatabaseError`, `DatabaseOperationalError`, `DatabaseSessionManager`, `DirtyStateError`, `EntityMappingError`, `FactRowMapper`, `FamilyRowMapper`, `IndividualRowMapper`, `LocationRowMapper`, `MIGRATION_REGISTRY`, `Migration`, `RecordNotFoundError`, `SchemaManager`, `SiteRowMapper`, `TransactionError`, `get_mapper`.

---
Generated dynamically by `src/system/gen_readme.py`.
