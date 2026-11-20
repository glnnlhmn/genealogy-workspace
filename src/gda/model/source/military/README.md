<!--Path: src/gda/model/source/military/README.md-->
# Military Source Records Suite (src/gda/model/source/military)

## Architectural Role
Evidentiary military source record models encompassing conscription, active service, pensions, bounty land, casualties, burials, and valor awards.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_military/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[awards/](awards/README.md)**: Military awards, valor decorations, unit citations, and campaign medals.
- **[casualty/](casualty/README.md)**: Military casualty reports, combat actions, prisoner of war records, and burials.
- **[draft/](draft/README.md)**: Military draft registration, militia enrollment, and selective service records.
- **[pension/](pension/README.md)**: Military pension applications, invalid disability claims, widow/dependent files,
- **[service/](service/README.md)**: Military service, enlistment, muster-in/out, CMSR, and discharge separation records.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Exports: `AwardScope`, `BountyLandAct`, `BountyLandWarrantRecord`, `CasualtyCategory`, `CivilWarConscriptionAllegiance`, `CivilWarDraftRecord`, `CivilWarEnrollmentClass`, `ColonialMilitiaClass`, `ColonialMilitiaRecord`, `ColonialWarPeriod`, `CombatCasualtyRecord`, `DraftCardTier`, `EnlistmentMusterRecord`, `IntermentCemeteryType`, `MilitaryAwardRecord`, `MilitaryAwardTier`, `MilitaryBranch`, `MilitaryBurialRecord`, `MilitaryCasualtyRecord`, `MilitaryDraftRecord`, `MilitaryPensionRecord`, `MilitaryServiceRecord`, `ModernDraftEra`, `ModernSelectiveServiceRecord`, `MusterRollType`, `PensionClaimantRole`, `PensionPaymentAuthority`, `PensionVeteranClaimRecord`, `PensionWidowDependentRecord`, `PowCampType`, `PrisonerOfWarRecord`, `SeparationCharacter`, `SeparationDischargeRecord`, `SeparationFormType`, `ServiceComponent`, `SssClassification`, `WwiCitizenshipStatus`, `WwiDraftCardRecord`, `WwiPhysicalDescription`, `WwiiDraftCardRecord`, `WwiiDraftWave`, `WwiiPhysicalMetrics`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 2d4d9a93b736cd8a -->
