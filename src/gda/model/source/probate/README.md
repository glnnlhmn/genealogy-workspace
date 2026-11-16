# Probate Wills & Estate Inventories (src/gda/model/source/probate)

## Architectural Role
Last wills and testaments, codicils, testamentary bequests, letters of administration, and itemized estate appraisals.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_probate/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `inventory.py` | `1.0.0+build.3` | Estate appraisal inventory, vendue list, and administration accounting models. |
| `will.py` | `1.0.0+build.3` | Last wills and testaments, codicils, letters testamentary/administration, and probate dockets. |

## Public Exports & Consumption Contract
Exports: `EstateInventoryRecord`, `InventoryLineItem`, `ProbateLedgerEntry`, `ProbateRecord`, `WillBequest`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
