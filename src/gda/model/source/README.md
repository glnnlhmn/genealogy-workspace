# Archival Documentary Source Record Suite (src/gda/model/source)

## Architectural Role
Unified Tier-3 documentary SourceRecord and EnumeratedRollRecord suite spanning all 12 historical and evidentiary domains.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[cemetery/](cemetery/README.md)**: Cemetery marker, monument, plot ledger, and grave survey domain models.
- **[education/](education/README.md)**: Historical diplomas, graduation certificates, yearbooks, and educational credentials.
- **[enumerated/](enumerated/README.md)**: Enumerated and tabulated archival source records (census, tax, and directory schedules).
- **[immigration/](immigration/README.md)**: Historical ship passenger arrival manifests, border crossings, and naturalization models.
- **[land/](land/README.md)**: Historical land deeds, conveyances, mortgages, patents, warrants, and survey models.
- **[manuscripts/](manuscripts/README.md)**: Family Bible vital registers, manuscript collections, correspondence, diaries, and narratives.
- **[military/](military/README.md)**: Authoritative military service, draft, pension, casualty, and awards domain models.
- **[orgs/](orgs/README.md)**: Organizational affiliation and enumerated membership roster source records.
- **[other/](other/README.md)**: Flexible catch-all models for miscellaneous historical records, ephemera, and untyped items.
- **[probate/](probate/README.md)**: Last wills and testaments, codicils, estate inventories, and probate accounting models.
- **[publications/](publications/README.md)**: Serial publications, newspaper clippings, periodicals, and published history models.
- **[vital/](vital/README.md)**: Vital and sacramental event record definitions.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Exports: `AcademicCredentialRecord`, `AgriculturalScheduleEntry`, `AgriculturalScheduleRecord`, `AssessedProperty`, `BaptismRecord`, `BibleRegisterEntry`, `BirthRecord`, `BountyLandWarrantRecord`, `CemeteryMarkerRecord`, `CemeteryPlotEntry`, `CemeteryRegistryRecord`, `CensusLineEntry`, `CensusScheduleRecord`, `CivilWarDraftRecord`, `ColonialMilitiaRecord`, `CombatCasualtyRecord`, `DeathRecord`, `DeedParty`, `DirectoryEntry`, `DirectoryRollRecord`, `DivorceRecord`, `EnlistmentMusterRecord`, `EnumeratedRollRecord`, `EstateInventoryRecord`, `FamilyBibleRecord`, `HouseholdTallyEntry`, `ImmigrationManifestRecord`, `InventoryLineItem`, `LandDeedRecord`, `LandGrantRecord`, `LandParcel`, `ManifestPassenger`, `ManufacturingScheduleEntry`, `ManufacturingScheduleRecord`, `MarkerInterment`, `MarriageRecord`, `MilitaryAwardRecord`, `MilitaryBurialRecord`, `MilitaryCasualtyRecord`, `MilitaryDraftRecord`, `MilitaryPensionRecord`, `MilitaryServiceRecord`, `ModernSelectiveServiceRecord`, `MortalityScheduleEntry`, `MortalityScheduleRecord`, `NarrativeManuscriptRecord`, `NaturalizationRecord`, `NaturalizationWitness`, `NewspaperClipRecord`, `OrganizationMembershipRecord`, `OrganizationRosterEntry`, `OrganizationRosterRecord`, `OtherMiscellaneousRecord`, `PensionVeteranClaimRecord`, `PensionWidowDependentRecord`, `PeriodicalArticleRecord`, `Population1850_1870Entry`, `Population1880Entry`, `Population1900_1910Entry`, `Population1920Entry`, `Population1930Entry`, `Population1940Entry`, `Population1950Entry`, `PopulationLineEntry`, `PopulationSchedule1790_1840`, `PopulationSchedule1850_1870`, `PopulationSchedule1880`, `PopulationSchedule1900_1910`, `PopulationSchedule1920`, `PopulationSchedule1930`, `PopulationSchedule1940`, `PopulationSchedule1950`, `PopulationScheduleRecord`, `PrisonerOfWarRecord`, `ProbateLedgerEntry`, `ProbateRecord`, `Publication`, `PublicationEntry`, `RegistryInterment`, `SeparationDischargeRecord`, `SeptennialCensusRecord`, `SlaveScheduleEntry`, `SlaveScheduleRecord`, `TaxAssessmentRecord`, `Veterans1890Entry`, `Veterans1890ScheduleRecord`, `WillBequest`, `WwiDraftCardRecord`, `WwiPhysicalDescription`, `WwiiDraftCardRecord`, `WwiiPhysicalMetrics`, `cemetery`, `education`, `enumerated`, `immigration`, `land`, `manuscripts`, `military`, `orgs`, `other`, `probate`, `publications`, `vital`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
