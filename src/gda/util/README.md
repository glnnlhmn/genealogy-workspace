# Identifier Minting, Text Sanitization & Phonetics (src/gda/util)

## Architectural Role
Pure helper algorithms for 6-digit SmartID and UUIDv4 minting/verification, high-water mark sequence extraction, Unicode/ASCII normalization, slugging, and historical phonetic encodings (Soundex, NYSIIS).

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_util/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `ids.py` | `1.0.0+build.13` | Stateless identifier minting, parsing, formatting, and validation helpers. |
| `text.py` | `1.0.0+build.16` | Pure stateless text normalization, slugging, and historical phonetic algorithms. |

## Public Exports & Consumption Contract
Exports: `clean_string`, `clean_whitespace`, `extract_max_smart_id`, `mint_smart_id`, `mint_uuid`, `normalize_ascii`, `parse_smart_id`, `phonetic_nysiis`, `phonetic_soundex`, `slugify`, `verify_id`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
