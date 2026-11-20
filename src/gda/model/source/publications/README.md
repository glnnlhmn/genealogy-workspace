<!--Path: src/gda/model/source/publications/README.md-->
# Newspapers, Periodicals & Bibliographic Catalogs (src/gda/model/source/publications)

## Architectural Role
Published newspaper clippings, obituaries, marriage/legal notices, periodical articles, and master publication catalog entries.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_publications/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `newspaper.py` | `1.0.0+build.3` | Newspaper article, obituary, vital notice, and clipping domain models. |
| `periodical.py` | `1.0.0+build.3` | Periodical article, school yearbook, commencement program, and published history models. |
| `publication.py` | `1.0.0+build.3` | Master serial, newspaper, periodical, and monograph publication source container models. |

## Public Exports & Consumption Contract
Exports: `NewspaperClipRecord`, `PeriodicalArticleRecord`, `Publication`, `PublicationEntry`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 8bf7d668f3e70522 -->
