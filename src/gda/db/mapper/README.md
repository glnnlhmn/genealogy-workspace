<!--Path: src/gda/db/mapper/README.md-->
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
| `base.py` | `1.0.0+build.5` | Base contract and shared serialization helpers for GDA SQLite row mappers. |
| `education_manuscripts_orgs_other.py` | `1.0.0+build.2` | Bidirectional SQLite row mappers for Education, Manuscripts, Orgs, and Other |
| `enumerated_publications.py` | `1.0.0+build.4` | Bidirectional SQLite row mappers for Enumerated and Publications source records. |
| `facts.py` | `1.0.0+build.2` | Bidirectional SQLite row mapper for Fact domain entities. |
| `immigration_military.py` | `1.0.0+build.8` | Bidirectional and polymorphic SQLite row mappers for Immigration and Military sources. |
| `organizations.py` | `1.0.0+build.1` | Bidirectional SQLite row mapper for Organization domain entities. |
| `personas.py` | `1.0.0+build.1` | Bidirectional SQLite row mappers for Individual and Family entities. |
| `places.py` | `1.0.0+build.1` | Bidirectional SQLite row mappers for Location and Site place entities. |
| `probate_land.py` | `1.0.0+build.3` | Bidirectional SQLite row mappers for Probate and Land archival source records. |
| `vital_cemetery.py` | `1.0.0+build.6` | Bidirectional SQLite row mappers for Vital and Cemetery archival source records. |
| `xref.py` | `1.0.0+build.2` | Bidirectional SQLite row mappers for Cross-Reference (gda.model.xref) models. |

## Public Exports & Consumption Contract
Exports: `AcademicCredentialRecordMapper`, `BaptismRecordMapper`, `BaseRowMapper`, `BirthRecordMapper`, `BountyLandWarrantRecordMapper`, `CemeteryMarkerRecordMapper`, `CemeteryRegistryRecordMapper`, `DeathRecordMapper`, `DirectoryRollRecordMapper`, `DivorceRecordMapper`, `EstateInventoryRecordMapper`, `FactParticipantXRefMapper`, `FactRowMapper`, `FamilyBibleRecordMapper`, `FamilyRowMapper`, `ImmigrationManifestRecordMapper`, `IndividualFamilyXRefMapper`, `IndividualOrganizationXRefMapper`, `IndividualRowMapper`, `IndividualSourceXRefMapper`, `IndividualSurnameXRefMapper`, `LandDeedRecordMapper`, `LandGrantRecordMapper`, `LocationRowMapper`, `LocationXRefMapper`, `MarriageRecordMapper`, `MediaXRefMapper`, `MilitaryAwardRecordMapper`, `MilitaryCasualtyRecordMapper`, `MilitaryDraftRecordMapper`, `MilitaryPensionRecordMapper`, `MilitaryServiceRecordMapper`, `NarrativeManuscriptRecordMapper`, `NaturalizationRecordMapper`, `NewspaperClipRecordMapper`, `OrganizationMembershipRecordMapper`, `OrganizationRosterRecordMapper`, `OrganizationRowMapper`, `OtherMiscellaneousRecordMapper`, `PeriodicalArticleRecordMapper`, `PopulationScheduleMapper`, `ProbateRecordMapper`, `PublicationMapper`, `SiteRowMapper`, `SiteXRefMapper`, `SupplementalScheduleMapper`, `SurnameXRefMapper`, `TaxAssessmentRecordMapper`, `_extract_id_str`, `_extract_year_from_text`, `get_mapper`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: a565e21e5f244db4 -->
