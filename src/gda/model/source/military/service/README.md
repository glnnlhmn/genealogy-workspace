<!--Path: src/gda/model/source/military/service/README.md-->
# Active Military Service & Discharge Records (src/gda/model/source/military/service)

## Architectural Role
Enlistment contracts, company muster rolls, naval service postings, and formal separation/discharge certificates.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_military/service/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.2` | Foundational military service record domain entity model. |
| `enlistment.py` | `1.0.0+build.2` | Enlistment contracts, muster rolls, and Compiled Military Service Records (CMSR). |
| `separation.py` | `1.0.0+build.2` | Discharge separation certificates and release records (DD-214, WD AGO). |

## Public Exports & Consumption Contract
Exports: `EnlistmentMusterRecord`, `MilitaryBranch`, `MilitaryServiceRecord`, `MusterRollType`, `SeparationCharacter`, `SeparationDischargeRecord`, `SeparationFormType`, `ServiceComponent`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 8d3321ecc6d148c9 -->
