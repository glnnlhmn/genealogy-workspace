# Kinship Graph & In-Memory Relationship Resolvers (src/gda/engine)

## Architectural Role
High-performance, in-memory graph resolution infrastructure providing O(1) kinship lookups, bidirectional media bindings, secondary event participant indexing, and safe entity eviction.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_engine/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **`kinship/`**: Kinship graph traversal, reciprocal calculations, and common ancestor discovery.
- **`plausibility/`**: Biological plausibility boundary audits and chronological validation rules.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `fact_resolver.py` | `1.0.0+build.1` | Active in-memory fact participant inverted indexer and relationship resolver. |
| `media_resolver.py` | `1.0.0+build.2` | Active in-memory media graph indexer and bidirectional resolver. |
| `resolver.py` | `1.0.0+build.3` | Active in-memory graph indexers and bidirectional relationship resolvers. |

## Public Exports & Consumption Contract
Exports: `FactParticipantResolver`, `IndividualFamilyResolver`, `MediaXRefResolver`.

---
Generated dynamically by `src/system/gen_readme.py`.
