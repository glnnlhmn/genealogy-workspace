<!--Path: src/gda/model/source/vital/README.md-->
# Civil & Ecclesiastical Vital Records (src/gda/model/source/vital)

## Architectural Role
Civil and parish birth, baptism, marriage, divorce, and death certificates and register entries.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_vital/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `baptism.py` | `1.0.0+build.4` | Ecclesiastical baptismal, christening, and cradle roll record models. |
| `birth.py` | `1.0.0+build.4` | Civil and hospital birth certificate and birth register domain models. |
| `death.py` | `1.0.0+build.5` | Civil death certificate, coroner inquest, transit permit, and death register models. |
| `divorce.py` | `1.0.0+build.3` | Civil divorce decree, divorce report, docket entry, and annulment models. |
| `marriage.py` | `1.0.0+build.5` | Civil and ecclesiastical marriage license, certificate, bond, and register models. |

## Public Exports & Consumption Contract
Exports: `BaptismRecord`, `BirthRecord`, `DeathRecord`, `DivorceRecord`, `MarriageRecord`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 6b78befe0abf6064 -->
