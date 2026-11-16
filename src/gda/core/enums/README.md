# Authoritative Enumeration Domains (src/gda/core/enums)

## Architectural Role
Authoritative genealogical enumerations inheriting from StrEnum and IntEnum, governing biological sex, evidentiary certainty (QuayScore), events, jurisdictions, organizations, and archival classifications.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_core/test_enums/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `archival.py` | `1.0.0+build.1` | Controlled enumerations for physical documents, transcripts, and archival artifacts. |
| `core.py` | `1.0.0+build.3` | Foundational domain classifications, assessment metrics, and certainty scores. |
| `date.py` | `1.0.0+build.1` | Standardized historical temporal and census enumeration classifications. |
| `fiscal.py` | `1.0.0+build.1` | Economic, real property tenure, directory status, and tax classification enums. |
| `immigration.py` | `1.0.0+build.1` | Immigration voyage passage classes and naturalization proceeding stages. |
| `land.py` | `1.0.0+build.1` | Real-property conveyance party roles and public-domain land grant basis enums. |
| `location.py` | `1.0.0+build.1` | Categorical enumerations for jurisdictional boundaries and administrative tiers. |
| `military.py` | `1.0.0+build.1` | Military domain enumerations across service, awards, casualty, pension, and draft records. |
| `orgs.py` | `1.0.0+build.1` | Categorical enumerations for voluntary associations, religious bodies, and societies. |
| `probate.py` | `1.0.0+build.1` | Probate bequest, estate inventory property, and administration accounting enums. |
| `site.py` | `1.0.0+build.1` | Spatial jurisdiction levels, facility venues, and cemetery marker enums. |
| `sources.py` | `1.0.0+build.2` | Source record categories, document classifications, and historical schedules. |
| `vital.py` | `1.0.0+build.1` | Demographic statuses, vital event assertions, and domestic relations enums. |

## Public Exports & Consumption Contract
Exports: `AffiliationType`, `ArrivalPassageClass`, `AssociatedRole`, `AwardScope`, `BequestType`, `BirthPlurality`, `BountyLandAct`, `CasualtyCategory`, `CensusYearUS`, `CitizenshipStatus`, `CivilWarConscriptionAllegiance`, `CivilWarEnrollmentClass`, `ColonialMilitiaClass`, `ColonialWarPeriod`, `DateModifier`, `DeedPartyRole`, `DispositionType`, `DivorceDecreeType`, `DocumentSide`, `DraftCardTier`, `EducationLevel`, `EstatePropertyCategory`, `EyeColor`, `FactType`, `HairColor`, `HistoricNameType`, `HomeOwnership`, `IDType`, `IntermentCemeteryType`, `JurisdictionCategory`, `LandGrantBasis`, `LegalPlaintiff`, `Legibility`, `LocationType`, `MODIFIER_ALIASES`, `MannerOfDeath`, `MaritalHistoryDissolution`, `MaritalStatus`, `MarkerCondition`, `MarkerMaterial`, `MarkerType`, `MembershipStatus`, `MilitaryAwardTier`, `MilitaryBranch`, `MilitaryConflict`, `MilitaryDraftType`, `MilitaryWar`, `ModernDraftEra`, `MusterRollType`, `NaturalizationStage`, `NoteType`, `OperationalStatus`, `OrganizationCategory`, `PedigreeType`, `PensionClaimantRole`, `PensionPaymentAuthority`, `PhysicalBuild`, `PowCampType`, `ProbateLedgerEntryKind`, `PublicationFrequency`, `QualityAssessment`, `QuayScore`, `ResidentialStatus`, `SelectiveServiceClass`, `SeparationCharacter`, `SeparationFormType`, `ServiceComponent`, `Sex`, `SiteType`, `SmartIDPrefix`, `SourceRecordCategory`, `SourceRecordType`, `SssClassification`, `TaxpayerClassification`, `TestimonyMedium`, `TextQuality`, `TranscriptLegibility`, `UnionDissolutionType`, `UnionType`, `VitalModifier`, `WwiCardType`, `WwiCitizenshipStatus`, `WwiiDraftWave`, `normalize_modifier`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
