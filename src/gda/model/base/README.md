<!--Path: src/gda/model/base/README.md-->
# Composite Base Value Objects & Entity Envelopes (src/gda/model/base)

## Architectural Role
Reusable Tier-1 and Tier-2 composite building blocks: audit stamps, soft-deprecation tombstones, personal/institutional names, notes, media, transcripts, source citations, base entity classes, and registry envelopes.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_base/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `address.py` | `1.0.0+build.1` | Structured postal address representation using Pydantic dataclasses. |
| `age.py` | `1.0.0+build.1` | Age record representation using Pydantic dataclasses. |
| `association.py` | `1.0.0+build.1` | Associated participant representation using Pydantic dataclasses. |
| `audit.py` | `1.0.0+build.6` | Immutable temporal audit stamping for archive records and entities. |
| `date.py` | `1.0.0+build.2` | Composite historical event dates and temporal bounding ranges. |
| `entity.py` | `1.0.0+build.7` | Foundational base entity schemas and lifecycle mixin for domain entities and assets. |
| `envelope.py` | `1.0.0+build.1` | Administrative collection envelope using Pydantic dataclasses. |
| `family.py` | `1.0.0+build.1` | Relational value objects representing domestic unions and pedigree linkages. |
| `geo.py` | `1.0.0+build.1` | Composite geospatial coordinate base structures. |
| `media.py` | `1.0.0+build.1` | Digital media asset metadata representation using Pydantic dataclasses. |
| `name.py` | `1.0.0+build.7` | Onomastic domain composites for personal names and historical entity appellations. |
| `note.py` | `1.0.0+build.5` | Embedded research note value object for entities and archival records. |
| `source.py` | `1.0.0+build.10` | Foundational documentary source citations, metadata headers, and base record models. |
| `tombstone.py` | `1.0.0+build.7` | Generic soft-deletion and record-supersession tombstone lifecycle primitives. |
| `transcript.py` | `1.0.0+build.4` | Archival text transcription and abstract composite value object. |

## Public Exports & Consumption Contract
Exports: `Address`, `Age`, `AssociatedIndividual`, `AuditStamp`, `BaseEntity`, `BaseEntityGUID`, `CanonicalName`, `ChildLink`, `Coordinates`, `DocumentSide`, `EntityLifecycleMixin`, `EventDate`, `FamilyUnion`, `HistoricVariant`, `HistoricalName`, `Legibility`, `Media`, `NameBase`, `NameLifecycleMixin`, `NamePerson`, `NameThing`, `Note`, `RecordMetadata`, `RegistryEnvelope`, `SourceRecord`, `SourceReference`, `TextQuality`, `TimePeriod`, `Tombstone`, `Transcript`, `is_tombstoned`, `stamp_tombstone`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 9752d841b76a0a4f -->
