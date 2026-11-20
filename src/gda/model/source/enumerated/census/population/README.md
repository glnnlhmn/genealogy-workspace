<!--Path: src/gda/model/source/enumerated/census/population/README.md-->
# US Federal Population Schedules 1790-1950 (src/gda/model/source/enumerated/census/population)

## Architectural Role
Era-specific US Federal Census population schedule records and household/person line entries from 1790 through 1950.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_enumerated/census/population/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.2` | Base population schedule domain models for decennial population enumerations. |
| `schedule_1850_1870.py` | `1.0.0+build.2` | Mid-century U.S. Federal Population Schedule domain models (1850, 1860, 1870). |
| `schedule_1880.py` | `1.0.0+build.2` | Tenth U.S. Federal Population Schedule domain models (1880). |
| `schedule_1900_1910.py` | `1.0.0+build.2` | Twelfth and Thirteenth U.S. Federal Population Schedule domain models (1900, 1910). |
| `schedule_1920.py` | `1.0.0+build.2` | Fourteenth U.S. Federal Population Schedule domain models (1920). |
| `schedule_1930.py` | `1.0.0+build.2` | Fifteenth U.S. Federal Population Schedule domain models (1930). |
| `schedule_1940.py` | `1.0.0+build.2` | Sixteenth U.S. Federal Population Schedule domain models (1940). |
| `schedule_1950.py` | `1.0.0+build.2` | Seventeenth U.S. Federal Population Schedule domain models (1950). |
| `tally_1790_1840.py` | `1.0.0+build.2` | Pre-1850 U.S. Federal Population Schedule domain models (1790-1840). |

## Public Exports & Consumption Contract
Exports: `HouseholdTallyEntry`, `Population1850_1870Entry`, `Population1880Entry`, `Population1900_1910Entry`, `Population1920Entry`, `Population1930Entry`, `Population1940Entry`, `Population1950Entry`, `PopulationLineEntry`, `PopulationSchedule1790_1840`, `PopulationSchedule1850_1870`, `PopulationSchedule1880`, `PopulationSchedule1900_1910`, `PopulationSchedule1920`, `PopulationSchedule1930`, `PopulationSchedule1940`, `PopulationSchedule1950`, `PopulationScheduleRecord`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 7cf5d5d3b078421c -->
