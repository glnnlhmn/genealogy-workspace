# Utility Algorithms & Text Normalizers (src/gda/util)

## Architectural Role
High-performance phonetics algorithms (Soundex, NYSIIS), cryptographic hashing routines, identifier generators, and text sanitizers.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_util/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `dates.py` | `0.0.1+build.1` | ISO date and timestamp format definitions, regex patterns, and string validators. |
| `hashes.py` | `0.0.1+build.1` | Pure stateless hashing utilities and checksum validators. |
| `ids.py` | `0.0.1+build.1` | Stateless identifier minting, parsing, formatting, and validation helpers. |
| `text.py` | `0.0.1+build.r15` | Pure stateless text normalization, slugging, and historical phonetic algorithms. |

## Public Exports & Consumption Contract
Modules export public interfaces explicitly declared in `__all__`.

---
Generated dynamically by `src/system/generate_readmes.py`.
