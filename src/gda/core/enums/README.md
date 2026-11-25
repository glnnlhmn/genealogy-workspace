<!--Path: src/gda/core/enums/README.md-->
# Authoritative Enumeration Domains (src/gda/core/enums)

## Architectural Role
Authoritative genealogical enumerations inheriting from GDAStrEnum and GDAIntEnum with canonical coercion primitives, governing biological sex, evidentiary certainty (QuayScore), events, jurisdictions, organizations, military, vital, and archival classifications.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_core/test_enums/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `archival.py` | `1.0.0+build.2` | Controlled enumerations for physical documents, transcripts, and archival artifacts. |
| `base.py` | `1.0.0+build.1` | Tier 0 base classes for all GDA string and integer enumerations. |
| `coercion.py` | `1.0.0+build.2` | Canonical Tier 0 enum coercion and token normalization utilities. |
| `core.py` | `1.0.0+build.4` | Foundational domain classifications, assessment metrics, and certainty scores. |
| `date.py` | `1.0.0+build.2` | Standardized historical temporal and census enumeration classifications. |
| `fiscal.py` | `1.0.0+build.2` | Fiscal, taxation, housing tenure, and citizenship status enumerations. |
| `immigration.py` | `1.0.0+build.2` | Immigration voyage passage classes and naturalization proceeding stages. |
| `land.py` | `1.0.0+build.2` | Real-property conveyance party roles and public-domain land grant basis enums. |
| `location.py` | `1.0.0+build.2` | Categorical enumerations for jurisdictional boundaries and administrative tiers. |
| `military.py` | `1.0.0+build.3` | Military domain enumerations across service, awards, casualty, pension, and draft records. |
| `orgs.py` | `1.0.0+build.2` | Categorical enumerations for voluntary associations, religious bodies, and societies. |
| `probate.py` | `1.0.0+build.2` | Probate bequest, estate inventory property, and administration accounting enums. |
| `site.py` | `1.0.0+build.2` | Spatial jurisdiction levels, facility venues, and cemetery marker enums. |
| `sources.py` | `1.0.0+build.3` | Source record categories and granular document classifications. |
| `vital.py` | `1.0.0+build.2` | Demographic statuses, vital event assertions, biographical traits, and domestic relations enums. |

## Public Exports & Consumption Contract
Exports: `AffiliationType`, `ArrivalPassageClass`, `AssociatedRole`, `AwardScope`, `BequestType`, `BirthPlurality`, `BountyLandAct`, `CasualtyCategory`, `CensusYearUS`, `CitizenshipStatus`, `CivilWarConscriptionAllegiance`, `CivilWarEnrollmentClass`, `ColonialMilitiaClass`, `ColonialWarPeriod`, `DateModifier`, `DeedPartyRole`, `DispositionType`, `DivorceDecreeType`, `DocumentSide`, `DraftCardTier`, `EducationLevel`, `EstatePropertyCategory`, `EyeColor`, `FactType`, `GDAIntEnum`, `GDAStrEnum`, `HairColor`, `HistoricNameType`, `HomeOwnership`, `IDType`, `IntermentCemeteryType`, `JurisdictionCategory`, `LandGrantBasis`, `LegalPlaintiff`, `Legibility`, `LocationType`, `MODIFIER_ALIASES`, `MannerOfDeath`, `MaritalStatus`, `MarkerCondition`, `MarkerMaterial`, `MarkerType`, `MembershipStatus`, `MilitaryAwardTier`, `MilitaryBranch`, `MilitaryDraftType`, `MilitaryWar`, `ModernDraftEra`, `MusterRollType`, `NaturalizationStage`, `NoteType`, `OperationalStatus`, `OrganizationCategory`, `PedigreeType`, `PensionClaimantRole`, `PensionPaymentAuthority`, `PhysicalBuild`, `PowCampType`, `ProbateLedgerEntryKind`, `PublicationFrequency`, `QualityAssessment`, `QuayScore`, `ResidentialStatus`, `SeparationCharacter`, `SeparationFormType`, `ServiceComponent`, `Sex`, `SiteType`, `SmartIDPrefix`, `SourceRecordCategory`, `SourceRecordType`, `SssClassification`, `TaxpayerClassification`, `TestimonyMedium`, `TextQuality`, `UnionDissolutionType`, `UnionType`, `VitalModifier`, `WwiCardType`, `WwiCitizenshipStatus`, `WwiiDraftWave`, `coerce_enum`, `normalize_modifier`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 116803765a77158d -->
