<!--Path: src/gda/model/source/enumerated/taxes/README.md-->
# Tax Assessment & Septennial Rolls (src/gda/model/source/enumerated/taxes)

## Architectural Role
Real and personal property tax assessment rolls, poll tax lists, and Pennsylvania Septennial Census enumerations.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_enumerated/taxes/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `base.py` | `1.0.0+build.3` | Historical tax assessment and fiscal valuation roll domain models. |
| `septennial.py` | `1.0.0+build.2` | Pennsylvania Septennial Census, Freemen List, and Exoneration List models. |

## Public Exports & Consumption Contract
Exports: `AssessedProperty`, `SeptennialCensusRecord`, `TaxAssessmentRecord`, `TaxpayerClassification`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 4f5ce1c98a3fea4c -->
