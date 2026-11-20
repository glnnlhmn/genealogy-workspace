<!--Path: src/gda/model/source/military/draft/README.md-->
# Military Conscription & Draft Registrations (src/gda/model/source/military/draft)

## Architectural Role
Colonial militia rolls, Civil War draft consolidations, WWI and WWII draft registration cards, and modern Selective Service records.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_military/draft/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.2` | Domain entity model representing military conscription registration records. |
| `civil_war.py` | `1.0.0+build.2` | Civil War military draft and enrollment record domain entity model. |
| `colonial.py` | `1.0.0+build.2` | Colonial and Revolutionary War militia enrollment and levy record domain entity. |
| `modern_sss.py` | `1.0.0+build.2` | Post-WWII and modern Selective Service System (SSS) draft registration model. |
| `wwi.py` | `1.0.0+build.2` | World War I military draft registration card domain entity model. |
| `wwii.py` | `1.0.0+build.2` | World War II military draft registration card domain entity model. |

## Public Exports & Consumption Contract
Exports: `CivilWarConscriptionAllegiance`, `CivilWarDraftRecord`, `CivilWarEnrollmentClass`, `ColonialMilitiaClass`, `ColonialMilitiaRecord`, `ColonialWarPeriod`, `DraftCardTier`, `MilitaryDraftRecord`, `ModernDraftEra`, `ModernSelectiveServiceRecord`, `SssClassification`, `WwiCitizenshipStatus`, `WwiDraftCardRecord`, `WwiPhysicalDescription`, `WwiiDraftCardRecord`, `WwiiDraftWave`, `WwiiPhysicalMetrics`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: b5c23541acdd5dd9 -->
