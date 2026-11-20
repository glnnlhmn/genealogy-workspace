<!--Path: src/gda/db/README.md-->
# Database Persistence, Session Lifecycle & Mapping Layer (src/gda/db)

## Architectural Role
SQLite persistence foundation uniting DatabaseSessionManager (WAL mode, foreign keys, atomic transactions, nested savepoints), SchemaManager, modular analytical DDL migrations, bidirectional entity RowMappers, and the DatabaseError hierarchy.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_db/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[mapper/](mapper/README.md)**: Public facade and registry for GDA bidirectional SQLite row mappers.
- **[schema/](schema/README.md)**: Schema management facade for GDA persistence layer.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `exceptions.py` | `1.0.0+build.4` | Database persistence exception hierarchy for the Genealogy Digital Archive. |
| `session.py` | `1.0.0+build.9` | SQLite connection lifecycle and atomic transaction management for GDA. |

## Public Exports & Consumption Contract
Exports: `BaseRowMapper`, `ConnectionTimeoutError`, `ConstraintViolationError`, `DatabaseConnectionError`, `DatabaseError`, `DatabaseOperationalError`, `DatabaseSessionManager`, `DirtyStateError`, `EntityMappingError`, `FactRowMapper`, `FamilyRowMapper`, `IndividualRowMapper`, `LocationRowMapper`, `MIGRATION_REGISTRY`, `Migration`, `OrganizationRowMapper`, `RecordNotFoundError`, `SchemaManager`, `SchemaMigrationError`, `SiteRowMapper`, `TransactionError`, `get_mapper`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: c7fc34b313dfb2f9 -->
