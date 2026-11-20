<!--Path: src/gda/util/README.md-->
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
| `enums.py` | `1.0.0+build.3` | Generic controlled-vocabulary enumeration coercion utilities. |
| `ids.py` | `1.0.0+build.16` | Stateless identifier minting, parsing, formatting, and validation helpers. |
| `text.py` | `1.0.0+build.17` | Pure stateless text normalization, slugging, and historical phonetic algorithms. |

## Public Exports & Consumption Contract
Exports: `clean_string`, `clean_unique_strings`, `clean_whitespace`, `coerce_enum`, `extract_max_smart_id`, `mint_smart_id`, `mint_uuid`, `normalize_ascii`, `normalize_id`, `parse_smart_id`, `phonetic_nysiis`, `phonetic_soundex`, `require_non_empty`, `resolve_polymorphic_id`, `slugify`, `unwrap_bool_int`, `unwrap_int`, `unwrap_value`, `verify_id`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 3f6b8246343daeba -->
