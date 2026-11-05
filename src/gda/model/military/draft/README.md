# Military Conscription & Draft Registrations (src/gda/model/military/draft)

## Architectural Role
Historical draft registrations, militia enrollment lists, Civil War enrollment, and modern Selective Service records.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_military/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.3` | Domain entity model representing military conscription registration records. |
| `civil_war.py` | `1.0.0+build.1` | Civil War military draft and enrollment record domain entity model. |
| `colonial.py` | `1.0.0+build.1` | Colonial and Revolutionary War militia enrollment and levy record domain entity. |
| `modern_sss.py` | `1.0.0+build.1` | Post-WWII and modern Selective Service System (SSS) draft registration model. |
| `wwi.py` | `1.0.0+build.1` | World War I military draft registration card domain entity model. |
| `wwii.py` | `1.0.0+build.1` | World War II military draft registration card domain entity model. |

## Public Exports & Consumption Contract
Exports: `CivilWarConscriptionAllegiance`, `CivilWarDraftRecord`, `CivilWarEnrollmentClass`, `ColonialMilitiaClass`, `ColonialMilitiaRecord`, `ColonialWarPeriod`, `DraftCardTier`, `MilitaryDraftRecord`, `ModernDraftEra`, `ModernSelectiveServiceRecord`, `SssClassification`, `WwiCitizenshipStatus`, `WwiDraftCardRecord`, `WwiPhysicalDescription`, `WwiiDraftCardRecord`, `WwiiDraftWave`, `WwiiPhysicalMetrics`.

---
Generated dynamically by `src/system/gen_readme.py`.
