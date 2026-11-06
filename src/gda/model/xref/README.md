# Cross-Reference & Relational Edge Models (src/gda/model/xref)

## Architectural Role
Decoupled, immutable relational edge dataclasses connecting personas, domestic family units, secondary event participants, and digital media assets with deterministic compound primary keys.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_xref/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `fact_participant_xref.py` | `1.0.0+build.1` | Associative relational edge linking individuals to facts in participant roles. |
| `individual_family_xref.py` | `1.0.0+build.1` | Relational kinship cross-reference edge linking individuals and family units. |
| `media_xref.py` | `1.0.0+build.4` | Associative relational cross-reference edge linking domain entities to media assets. |

## Public Exports & Consumption Contract
Exports: `FactParticipantXRef`, `IndividualFamilyXRef`, `MediaXRef`.

---
Generated dynamically by `src/system/gen_readme.py`.
