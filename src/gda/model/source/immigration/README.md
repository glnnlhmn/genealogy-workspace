<!--Path: src/gda/model/source/immigration/README.md-->
# Passenger Manifests & Naturalization Records (src/gda/model/source/immigration)

## Architectural Role
Ship passenger arrival manifests, border crossings, declarations of intention, petitions, and naturalization certificates.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_immigration/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `manifest.py` | `1.0.0+build.5` | Historical ship passenger arrival manifests, customs lists, border crossings, and crew lists. |
| `naturalization.py` | `1.0.0+build.6` | Historical naturalization declarations of intention, petitions, oaths, and certificates. |

## Public Exports & Consumption Contract
Exports: `ImmigrationManifestRecord`, `ManifestPassenger`, `NaturalizationRecord`, `NaturalizationWitness`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 1fadf873bda25580 -->
