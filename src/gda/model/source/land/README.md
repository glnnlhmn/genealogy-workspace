# Land Deeds, Conveyances & Sovereign Grants (src/gda/model/source/land)

## Architectural Role
Real property deeds, grantor/grantee conveyances, metes-and-bounds / PLSS parcel descriptions, and sovereign land patents.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_land/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `deed.py` | `1.0.0+build.3` | Historical land deeds, indentures, quitclaims, mortgages, sheriff's deeds, and dower releases. |
| `grant.py` | `1.0.0+build.3` | Sovereign land grants, patents, land warrants, bounty land claims, and metes-and-bounds surveys. |

## Public Exports & Consumption Contract
Exports: `DeedParty`, `LandDeedRecord`, `LandGrantRecord`, `LandParcel`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
