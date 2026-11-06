# Military Valor & Service Awards (src/gda/model/military/awards)

## Architectural Role
Valor citations, campaign medals, unit commendations, wound badges, and decoration claim models.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_military/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.1` | Military awards, decorations, citations, and campaign medal entity records. |

## Public Exports & Consumption Contract
Exports: `AwardScope`, `MilitaryAwardRecord`, `MilitaryAwardTier`.

---
Generated dynamically by `src/system/gen_readme.py`.
