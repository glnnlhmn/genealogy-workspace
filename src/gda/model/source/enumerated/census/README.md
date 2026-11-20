<!--Path: src/gda/model/source/enumerated/census/README.md-->
# Census Schedule Foundations (src/gda/model/source/enumerated/census)

## Architectural Role
Shared base abstractions and enumeration district metadata for population and non-population census schedules.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_enumerated/census/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[population/](population/README.md)**: Decennial U.S. Federal Population Schedule models across historical eras (1790-1950).
- **[supplemental/](supplemental/README.md)**: Non-population federal census schedule models (mortality, agricultural, manufacturing, slave, veterans).

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.5` | Foundational census schedule and row-level line entry domain models. |

## Public Exports & Consumption Contract
Exports: `AgriculturalScheduleEntry`, `AgriculturalScheduleRecord`, `CensusLineEntry`, `CensusScheduleRecord`, `HouseholdTallyEntry`, `ManufacturingScheduleEntry`, `ManufacturingScheduleRecord`, `MortalityScheduleEntry`, `MortalityScheduleRecord`, `Population1850_1870Entry`, `Population1880Entry`, `Population1900_1910Entry`, `Population1920Entry`, `Population1930Entry`, `Population1940Entry`, `Population1950Entry`, `PopulationLineEntry`, `PopulationSchedule1790_1840`, `PopulationSchedule1850_1870`, `PopulationSchedule1880`, `PopulationSchedule1900_1910`, `PopulationSchedule1920`, `PopulationSchedule1930`, `PopulationSchedule1940`, `PopulationSchedule1950`, `PopulationScheduleRecord`, `SlaveScheduleEntry`, `SlaveScheduleRecord`, `Veterans1890Entry`, `Veterans1890ScheduleRecord`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: f20b3720c843ee8a -->
