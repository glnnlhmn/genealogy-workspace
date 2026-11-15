# City, County & Occupational Directories (src/gda/model/source/enumerated/directories)

## Architectural Role
Historical city, county, and business directory roll records capturing residential addresses, occupations, and spousal listings.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_enumerated/directories/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.3` | City, business, farmers', and civic/voter directory enumeration models. |

## Public Exports & Consumption Contract
Exports: `DirectoryEntry`, `DirectoryRollRecord`, `ResidentialStatus`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
