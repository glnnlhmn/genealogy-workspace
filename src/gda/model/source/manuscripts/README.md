<!--Path: src/gda/model/source/manuscripts/README.md-->
# Family Bibles & Narrative Manuscripts (src/gda/model/source/manuscripts)

## Architectural Role
Inscribed family Bible vital registers, personal diaries, correspondence, and unpublished genealogical manuscripts.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_manuscripts/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `bible.py` | `1.0.0+build.3` | Family Bible vital registers and genealogical inscriptions. |
| `narrative.py` | `1.0.0+build.3` | Manuscript collections, personal correspondence, diaries, memoirs, depositions, and oral histories. |

## Public Exports & Consumption Contract
Exports: `BibleRegisterEntry`, `FamilyBibleRecord`, `NarrativeManuscriptRecord`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 4c8dc396d081f8f6 -->
