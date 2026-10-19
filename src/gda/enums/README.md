# Authoritative Enumeration Domains (src/gda/enums)

## Architectural Role
Authoritative genealogical enumerations inheriting strictly from StrEnum and IntEnum, governing biological sex, evidentiary certainty (QuayScore), events, jurisdictions, and archival classifications.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_enums/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `archival.py` | `0.1.0+build.r1` | Archival notes, transcription clarity, physical media orientation, and formats. |
| `core.py` | `0.2.0+build.5` | Foundational domain classifications, assessment metrics, and certainty scores. |
| `fiscal.py` | `0.1.0+build.r1` | Economic, real property tenure, directory status, and tax classification enums. |
| `site.py` | `0.1.0+build.r1` | Spatial jurisdiction levels, facility venues, and cemetery marker enums. |
| `sources.py` | `0.1.0+build.r1` | Source record categories, document classifications, and historical schedules. |
| `vital.py` | `0.1.0+build.4` | Demographic statuses, vital event assertions, and domestic relations enums. |

## Public Exports & Consumption Contract
Exports: `DocumentSide`, `NoteCategory`, `NoteType`, `PublicationFrequency`, `SelectiveServiceClass`, `TestimonyMedium`, `TranscriptLegibility`, `WwiCardType`, `AssociatedRole`, `DateModifier`, `FactType`, `QualityAssessment`, `QuayScore`, `Sex`, `VitalModifier`, `CitizenshipStatus`, `HomeOwnership`, `ResidentialStatus`, `TaxpayerClassification`, `LocationType`, `MarkerCondition`, `MarkerMaterial`, `MarkerType`, `OperationalStatus`, `SiteType`, `CensusYear`, `EducationLevel`, `MilitaryBranch`, `MilitaryConflict`, `MilitaryWar`, `SourceRecordCategory`, `SourceRecordType`, `BirthPlurality`, `DispositionType`, `DivorceDecreeType`, `LegalPlaintiff`, `MannerOfDeath`, `MaritalHistoryDissolution`, `MaritalStatus`, `PedigreeType`, `UnionDissolutionType`, `UnionType`, `NameStatus`.

---
Generated dynamically by `src/system/generate_readmes.py`.
