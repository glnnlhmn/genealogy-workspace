<!--Path: src/gda/model/source/enumerated/README.md-->
# Enumerated Schedules, Directories & Tax Rolls (src/gda/model/source/enumerated)

## Architectural Role
Multi-entry tabular roll and schedule records encompassing US Federal Census population and supplemental schedules, city/county directories, and tax assessment lists.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_enumerated/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[census/](census/README.md)**: Federal, state, and special census schedule source models.
- **[directories/](directories/README.md)**: City, business, farmers', and civic/voter directory enumeration records.
- **[taxes/](taxes/README.md)**: Historical tax assessment rolls, septennial censuses, and freemen/exoneration lists.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.9` | Foundational enumerated and tabulated archival roll domain entity model. |

## Public Exports & Consumption Contract
Exports: `AgriculturalScheduleEntry`, `AgriculturalScheduleRecord`, `AssessedProperty`, `CensusLineEntry`, `CensusScheduleRecord`, `DirectoryEntry`, `DirectoryRollRecord`, `EnumeratedRollRecord`, `HouseholdTallyEntry`, `ManufacturingScheduleEntry`, `ManufacturingScheduleRecord`, `MortalityScheduleEntry`, `MortalityScheduleRecord`, `Population1850_1870Entry`, `Population1880Entry`, `Population1900_1910Entry`, `Population1920Entry`, `Population1930Entry`, `Population1940Entry`, `Population1950Entry`, `PopulationLineEntry`, `PopulationSchedule1790_1840`, `PopulationSchedule1850_1870`, `PopulationSchedule1880`, `PopulationSchedule1900_1910`, `PopulationSchedule1920`, `PopulationSchedule1930`, `PopulationSchedule1940`, `PopulationSchedule1950`, `PopulationScheduleRecord`, `ResidentialStatus`, `SeptennialCensusRecord`, `SlaveScheduleEntry`, `SlaveScheduleRecord`, `TaxAssessmentRecord`, `TaxpayerClassification`, `Veterans1890Entry`, `Veterans1890ScheduleRecord`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: a5b57b23b8db79f4 -->
