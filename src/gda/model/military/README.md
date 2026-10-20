# Military Records Domain Package (src/gda/model/military)

## Architectural Role
Evidentiary military records domain model suite encompassing conscription and draft registrations, active duty muster/service/separation certificates, veteran invalid and widow/dependent pension claims, bounty land warrants, combat casualties, POW internments, national cemetery burials, and valor awards.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_military/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **`awards/`**: Military awards, valor decorations, unit citations, and campaign medals.
- **`casualty/`**: Military casualty reports, combat actions, prisoner of war records, and burials.
- **`draft/`**: Military draft registration, militia enrollment, and selective service records.
- **`pension/`**: Military pension applications, invalid disability claims, widow/dependent files,
- **`service/`**: Military service, enlistment, muster-in/out, CMSR, and discharge separation records.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Exports: `AwardScope`, `BountyLandAct`, `BountyLandWarrantRecord`, `CasualtyCategory`, `CivilWarConscriptionAllegiance`, `CivilWarDraftRecord`, `CivilWarEnrollmentClass`, `ColonialMilitiaClass`, `ColonialMilitiaRecord`, `ColonialWarPeriod`, `CombatCasualtyRecord`, `DraftCardTier`, `EnlistmentMusterRecord`, `IntermentCemeteryType`, `MilitaryAwardRecord`, `MilitaryAwardTier`, `MilitaryBranch`, `MilitaryBurialRecord`, `MilitaryCasualtyRecord`, `MilitaryDraftRecord`, `MilitaryPensionRecord`, `MilitaryServiceRecord`, `ModernDraftEra`, `ModernSelectiveServiceRecord`, `MusterRollType`, `PensionClaimantRole`, `PensionPaymentAuthority`, `PensionVeteranClaimRecord`, `PensionWidowDependentRecord`, `PowCampType`, `PrisonerOfWarRecord`, `SeparationCharacter`, `SeparationDischargeRecord`, `SeparationFormType`, `ServiceComponent`, `SssClassification`, `WwiCitizenshipStatus`, `WwiDraftCardRecord`, `WwiPhysicalDescription`, `WwiiDraftCardRecord`, `WwiiDraftWave`, `WwiiPhysicalMetrics`.

---
Generated dynamically by `src/system/generate_readmes.py`.
