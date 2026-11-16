# Supplemental & Non-Population Census Schedules (src/gda/model/source/enumerated/census/supplemental)

## Architectural Role
Agricultural, manufacturing, mortality, slave, and 1890 veterans supplemental census schedule records and line entries.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_enumerated/census/supplemental/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `agricultural.py` | `1.0.0+build.1` | Federal Census Productions of Agriculture Schedule domain models (1850-1880). |
| `manufacturing.py` | `1.0.0+build.1` | Federal Census Products of Industry / Manufacturing Schedule models (1810-1880). |
| `mortality.py` | `1.0.0+build.1` | Federal and state Census Mortality Schedule domain models (1850-1885). |
| `slave.py` | `1.0.0+build.1` | Federal Census Slave Schedule domain models (1850 & 1860). |
| `veterans_1890.py` | `1.0.0+build.1` | 1890 Special Schedule of Surviving Soldiers, Sailors, Marines, and Widows. |

## Public Exports & Consumption Contract
Exports: `AgriculturalScheduleEntry`, `AgriculturalScheduleRecord`, `ManufacturingScheduleEntry`, `ManufacturingScheduleRecord`, `MortalityScheduleEntry`, `MortalityScheduleRecord`, `SlaveScheduleEntry`, `SlaveScheduleRecord`, `Veterans1890Entry`, `Veterans1890ScheduleRecord`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
