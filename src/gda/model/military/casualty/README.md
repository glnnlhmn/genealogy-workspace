# Military Casualties, POW & Burials (src/gda/model/military/casualty)

## Architectural Role
Battlefield casualties, combat injury records, POW camp internments, and national cemetery burial records.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_military/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.1` | Foundational military casualty domain entity model. |
| `burial.py` | `1.0.0+build.1` | Military cemetery interments, national cemeteries, and government headstones. |
| `combat.py` | `1.0.0+build.1` | Battlefield combat casualty records (KIA, WIA, DOW, MIA). |
| `pow.py` | `1.0.0+build.1` | Prisoner of War (POW) internment, detention, and repatriation records. |

## Public Exports & Consumption Contract
Exports: `CasualtyCategory`, `CombatCasualtyRecord`, `IntermentCemeteryType`, `MilitaryBurialRecord`, `MilitaryCasualtyRecord`, `PowCampType`, `PrisonerOfWarRecord`.

---
Generated dynamically by `src/system/gen_readme.py`.
