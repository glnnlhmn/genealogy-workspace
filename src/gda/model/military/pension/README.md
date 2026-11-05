# Military Pensions & Bounty Land (src/gda/model/military/pension)

## Architectural Role
Veteran invalid claims, widow and minor dependent pensions, bounty land warrants, and acts of Congress pension files.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_military/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.1` | Foundational military pension domain entity model. |
| `bounty_land.py` | `1.0.0+build.1` | Federal and state military bounty land warrant application and patent records. |
| `veteran_claim.py` | `1.0.0+build.1` | Invalid veteran disability and service pension claim records. |
| `widow_dependent.py` | `1.0.0+build.2` | Surviving spouse, minor orphan, and dependent parent pension claim records. |

## Public Exports & Consumption Contract
Exports: `BountyLandAct`, `BountyLandWarrantRecord`, `MilitaryPensionRecord`, `PensionClaimantRole`, `PensionPaymentAuthority`, `PensionVeteranClaimRecord`, `PensionWidowDependentRecord`.

---
Generated dynamically by `src/system/gen_readme.py`.
