<!--Path: src/gda/model/source/military/awards/README.md-->
# Military Valor & Service Awards (src/gda/model/source/military/awards)

## Architectural Role
Valor citations, campaign medals, unit commendations, wound badges, and military decoration source records.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_military/awards/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.2` | Military awards, decorations, citations, and campaign medal entity records. |

## Public Exports & Consumption Contract
Exports: `AwardScope`, `MilitaryAwardRecord`, `MilitaryAwardTier`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 007b3193ad8846bb -->
