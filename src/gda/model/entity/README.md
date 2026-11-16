# Canonical Master Graph Entities (src/gda/model/entity)

## Architectural Role
Tier-3 master domain entities extending BaseEntity and enforcing relational integrity, temporal bounds, lineage hierarchies, and participant linkages (Fact, Family, Individual, Location, Organization, Site).

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_entity/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `fact.py` | `1.0.0+build.5` | Genealogical fact and life event entity model representing historical assertions. |
| `family.py` | `1.0.0+build.4` | Genealogical family entity model representing nuclear and domestic relations. |
| `individual.py` | `1.0.0+build.6` | Genealogical individual entity model extending BaseEntity[IndividualID]. |
| `location.py` | `1.0.0+build.3` | Jurisdictional boundary and administrative entity model. |
| `organization.py` | `1.0.0+build.2` | Voluntary association, fraternal society, religious body, and civic organization entity model. |
| `site.py` | `1.0.0+build.3` | Physical venue and archival site entity model implementations. |

## Public Exports & Consumption Contract
Exports: `Fact`, `FactParticipant`, `Family`, `Individual`, `Location`, `Organization`, `OrganizationEntityModel`, `Site`, `SiteEntityModel`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
