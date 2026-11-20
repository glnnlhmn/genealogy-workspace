<!--Path: src/gda/engine/README.md-->
# Package Documentation (src/gda/engine)

## Architectural Role
Architectural subsystem package.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_engine/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[kinship/](kinship/README.md)**: Kinship graph traversal, reciprocal calculations, and common ancestor discovery.
- **[plausibility/](plausibility/README.md)**: Biological plausibility boundary audits and chronological validation rules.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `fact_resolver.py` | `1.0.0+build.2` | Active in-memory fact participant inverted indexer and relationship resolver. |
| `media_resolver.py` | `1.0.0+build.3` | Active in-memory media graph indexer and bidirectional resolver. |
| `resolver.py` | `1.0.0+build.5` | Active in-memory graph indexers and bidirectional relationship resolvers. |

## Public Exports & Consumption Contract
Exports: `FactParticipantResolver`, `IndividualFamilyResolver`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: ff1c181a600b61b9 -->
