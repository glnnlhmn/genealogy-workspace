# Name: README.md
# Path: src/gda/enums/README.md

# Title: gda.enums

## Purpose
Provides authoritative, immutable controlled vocabulary definitions across the digital archive framework, partitioned into domain-specific modules (`core`, `sources`, `vital`, `site`, `archival`, and `fiscal`). Built on standard Python `StrEnum` and `IntEnum` to ensure native JSON serializability and direct Pydantic V2 validation without external framework dependencies.

---

## Architecture & Import Usage

All enumerations are exported at package root or can be imported directly from their respective domain modules:

- Direct root imports:
  from gda.enums import FactType, QuayScore, Sex, SourceRecordCategory

- Modular imports:
  from gda.enums.archival import NoteType, TranscriptLegibility
  from gda.enums.core import FactType, QuayScore, Sex
  from gda.enums.fiscal import HomeOwnership, TaxpayerClassification
  from gda.enums.site import LocationType, MarkerType, SiteType
  from gda.enums.sources import CensusYear, SourceRecordCategory, SourceRecordType
  from gda.enums.vital import MannerOfDeath, UnionStatus

---

## Enumeration Index

### 1. Core & Demographic Foundations (`gda.enums.core`)

| Enumeration | Type | Description |
| :--- | :--- | :--- |
| `AssociatedRole` | `StrEnum` | Standardized participant roles in associated person links (kinship, clerical, legal, informants). |
| `DateModifier` | `StrEnum` | Precision, boundary, and approximation modifiers for historical dates. |
| `FactType` | `StrEnum` | Canonical categories for historical event assertions and biographical facts. |
| `QualityAssessment` | `StrEnum` | Textual evidentiary rating evaluating archival record source reliability. |
| `QuayScore` | `IntEnum` | Standardized integer evidence certainty rating scale (0 to 3). |
| `Sex` | `StrEnum` | Canonical biological sex classifications (`M`, `F`, `U`). |
| `VitalModifier` | `StrEnum` | Vital status and life boundary precision modifiers (including living status). |

### 2. Sources, Schedules & Military History (`gda.enums.sources`)

| Enumeration | Type | Description |
| :--- | :--- | :--- |
| `CensusYear` | `IntEnum` | Historical decennial census population schedule years (1790–1950). |
| `EducationLevel` | `StrEnum` | Educational attainment levels and academic institution tiers. |
| `MilitaryBranch` | `StrEnum` | Standardized branches of the armed forces and organized militias. |
| `MilitaryConflict` | `StrEnum` | Historical conflict and draft era classification tokens. |
| `MilitaryWar` | `StrEnum` | Formal military war and theater classifications. |
| `SourceRecordCategory` | `StrEnum` | Primary archival source record domain categories. |
| `SourceRecordType` | `StrEnum` | Granular documentary source record types across all archival categories. |

### 3. Vital Events & Domestic Relations (`gda.enums.vital`)

| Enumeration | Type | Description |
| :--- | :--- | :--- |
| `BirthPlurality` | `StrEnum` | Plurality of birth recorded on birth certificates and registers. |
| `DispositionType` | `StrEnum` | Method and manner of mortal disposition recorded on death certificates. |
| `DivorceDecreeType` | `StrEnum` | Formal legal classification of divorce, separation, and annulment decrees. |
| `LegalPlaintiff` | `StrEnum` | Designation of the initiating party in domestic and legal civil proceedings. |
| `MannerOfDeath` | `StrEnum` | Categorical manner of death recorded by medical certifiers and coroners. |
| `MaritalHistoryDissolution` | `StrEnum` | Reported cause of prior marriage dissolution on marriage applications. |
| `MaritalStatus` | `StrEnum` | Marital status classifications recorded on census returns and vital records. |
| `UnionStatus` | `StrEnum` | Legal, biological, or ceremonial domestic partnership status. |

### 4. Spatial Jurisdictions & Physical Venues (`gda.enums.site`)

| Enumeration | Type | Description |
| :--- | :--- | :--- |
| `LocationType` | `StrEnum` | Civil and administrative jurisdictional levels (country, state, county, town). |
| `MarkerCondition` | `StrEnum` | Physical preservation and legibility state of cemetery markers and monuments. |
| `MarkerMaterial` | `StrEnum` | Material and lithic composition of cemetery memorials. |
| `MarkerType` | `StrEnum` | Architectural style and morphological typology of cemetery markers. |
| `OperationalStatus` | `StrEnum` | Operational lifecycle status of facilities, cemeteries, and physical sites. |
| `SiteType` | `StrEnum` | Physical venue and facility categories (cemeteries, churches, hospitals). |

### 5. Archival Notes & Source Media (`gda.enums.archival`)

| Enumeration | Type | Description |
| :--- | :--- | :--- |
| `DocumentSide` | `StrEnum` | Physical orientation and facing of archival documents, pages, and media. |
| `NoteCategory` | `StrEnum` | Workflow, transcription, discrepancy, and anomaly classification for notes. |
| `NoteType` | `StrEnum` | Primary contextual classification for archival research notes. |
| `PublicationFrequency` | `StrEnum` | Publication interval for serial newspapers and periodicals. |
| `SelectiveServiceClass` | `StrEnum` | Historical selective service military conscription classification codes. |
| `TestimonyMedium` | `StrEnum` | Physical recording medium and format of personal testimonies and memoirs. |
| `TranscriptLegibility` | `StrEnum` | Visual legibility assessment of written source transcriptions. |
| `WwiCardType` | `StrEnum` | Physical card version classification for WWI selective service registrations. |

### 6. Fiscal, Economic & Tenure Governance (`gda.enums.fiscal`)

| Enumeration | Type | Description |
| :--- | :--- | :--- |
| `CitizenshipStatus` | `StrEnum` | Legal citizenship and naturalization classifications on census returns. |
| `HomeOwnership` | `StrEnum` | Real property ownership and tenure status on census schedules. |
| `ResidentialStatus` | `StrEnum` | Occupancy and tenancy status in city directories and gazetteers. |
| `TaxpayerClassification` | `StrEnum` | Legal and socioeconomic classification of taxpayers on historical tax rolls. |