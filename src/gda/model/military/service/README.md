# Active Military Service & Enlistment (src/gda/model/military/service)

## Architectural Role
Enlistment oaths, company muster rolls, rank assignments, naval postings, and formal discharge certificates.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_military/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.4` | Foundational military service record domain entity model. |
| `enlistment.py` | `1.0.0+build.1` | Enlistment contracts, muster rolls, and Compiled Military Service Records (CMSR). |
| `separation.py` | `1.0.0+build.1` | Discharge separation certificates and release records (DD-214, WD AGO). |

## Public Exports & Consumption Contract
Exports: `EnlistmentMusterRecord`, `MilitaryBranch`, `MilitaryServiceRecord`, `MusterRollType`, `SeparationCharacter`, `SeparationDischargeRecord`, `SeparationFormType`, `ServiceComponent`.

---
Generated dynamically by `src/system/gen_readme.py`.
