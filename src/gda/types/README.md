# Data Types & Primitives (src/gda/types)

## Architectural Role
Foundational scalar primitives, string constraints, and custom Pydantic validators.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_types/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `primitives.py` | `0.0.1+build.2` | Authoritative regex patterns, format tokens, and primitive scalar definitions. |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `src/system/generate_readmes.py`.
