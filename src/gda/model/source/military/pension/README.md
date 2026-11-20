<!--Path: src/gda/model/source/military/pension/README.md-->
# Military Pensions & Bounty Land Warrants (src/gda/model/source/military/pension)

## Architectural Role
Veteran invalid pension claims, widow and dependent pension files, and military bounty land warrant applications.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_military/pension/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.2` | Foundational military pension domain entity model. |
| `bounty_land.py` | `1.0.0+build.2` | Federal and state military bounty land warrant application and patent records. |
| `veteran_claim.py` | `1.0.0+build.2` | Invalid veteran disability and service pension claim records. |
| `widow_dependent.py` | `1.0.0+build.2` | Surviving spouse, minor orphan, and dependent parent pension claim records. |

## Public Exports & Consumption Contract
Exports: `BountyLandAct`, `BountyLandWarrantRecord`, `MilitaryPensionRecord`, `PensionClaimantRole`, `PensionPaymentAuthority`, `PensionVeteranClaimRecord`, `PensionWidowDependentRecord`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 9cea9ea47bb6556f -->
