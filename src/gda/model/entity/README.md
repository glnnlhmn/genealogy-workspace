# Canonical Domain Entities (src/gda/model/entity)

## Architectural Role
Primary domain entities enforcing relational integrity, temporal bounds, biological plausibility, and participant linkages (Individual, Family, Fact, Location, Site).

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_entity/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `fact.py` | `1.0.0+build.6` | Genealogical fact and life event entity model representing historical assertions. |
| `family.py` | `1.0.0+build.2` | Genealogical family entity model representing nuclear and domestic relations. |
| `individual.py` | `1.0.0+build.8` | Genealogical individual entity model extending BaseEntity[IndividualID]. |
| `location.py` | `1.0.0+build.35` | Jurisdictional boundary and administrative entity model. |
| `site.py` | `1.0.0+build.7` | Physical venue and archival site entity model implementations. |

## Public Exports & Consumption Contract
Exports: `Fact`, `FactParticipant`, `Family`, `Individual`, `Location`, `Site`.

---
Generated dynamically by `src/system/gen_readme.py`.
