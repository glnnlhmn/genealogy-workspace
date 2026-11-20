<!--Path: src/gda/model/source/cemetery/README.md-->
# Cemetery Marker & Sexton Registry Records (src/gda/model/source/cemetery)

## Architectural Role
Gravestone marker transcriptions, multi-interment memorials, plot registries, and sexton burial ledger records.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_cemetery/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `marker.py` | `1.0.0+build.3` | Cemetery marker, headstone, monument, mausoleum crypt, and memorial inscription models. |
| `registry.py` | `1.0.0+build.3` | Cemetery plot ledger, sexton book, and grave survey registry domain models. |

## Public Exports & Consumption Contract
Exports: `CemeteryMarkerRecord`, `CemeteryPlotEntry`, `CemeteryRegistryRecord`, `MarkerInterment`, `RegistryInterment`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 9915f6ac68149b2e -->
