# Bidirectional Analytical Entity Row Mappers (src/gda/db/mapper)

## Architectural Role
Lossless bidirectional relational row-to-model mappers translating the six core domain entities (Location, Site, Organization, Individual, Family, Fact) to and from flattened SQLite rows.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_db/test_mapper/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.1` | Base contract and shared serialization helpers for GDA SQLite row mappers. |
| `facts.py` | `1.0.0+build.1` | Bidirectional SQLite row mapper for Fact domain entities. |
| `organizations.py` | `1.0.0+build.1` | Bidirectional SQLite row mapper for Organization domain entities. |
| `personas.py` | `1.0.0+build.1` | Bidirectional SQLite row mappers for Individual and Family entities. |
| `places.py` | `1.0.0+build.1` | Bidirectional SQLite row mappers for Location and Site place entities. |

## Public Exports & Consumption Contract
Exports: `BaseRowMapper`, `FactRowMapper`, `FamilyRowMapper`, `IndividualRowMapper`, `LocationRowMapper`, `OrganizationRowMapper`, `SiteRowMapper`, `_extract_id_str`, `_extract_year_from_text`, `get_mapper`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
