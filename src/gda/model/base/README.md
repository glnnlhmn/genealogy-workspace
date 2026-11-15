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
| `audit.py` | `1.0.0+build.1` | Core audit metadata tracking stamp using Pydantic dataclasses. |
| `date.py` | `1.0.0+build.2` | Composite historical event dates and temporal bounding ranges. |
| `entity.py` | `1.0.0+build.1` | Foundational base entity schemas and lifecycle mixin for domain entities and assets. |
| `envelope.py` | `1.0.0+build.1` | Administrative collection envelope using Pydantic dataclasses. |
| `family.py` | `1.0.0+build.1` | Relational value objects representing domestic unions and pedigree linkages. |
| `geo.py` | `1.0.0+build.1` | Composite geospatial coordinate base structures. |
| `media.py` | `1.0.0+build.1` | Digital media asset metadata representation using Pydantic dataclasses. |
| `name.py` | `1.0.0+build.2` | Canonical personal, jurisdictional, artifact, and historical naming representations. |
| `note.py` | `1.0.0+build.1` | Archival research note representation using Pydantic dataclasses. |
| `source.py` | `1.0.0+build.1` | Canonical source composites, citation pointers, and archival metadata headers. |
| `tombstone.py` | `1.0.0+build.1` | In-place entity lifecycle and deprecation tombstone using Pydantic dataclasses. |
| `transcript.py` | `1.0.0+build.1` | Full-text transcription and abstract representation using Pydantic dataclasses. |

## Public Exports & Consumption Contract
Exports: `Address`, `Age`, `AssociatedIndividual`, `AuditStamp`, `BaseEntity`, `BaseEntityGUID`, `CanonicalName`, `ChildLink`, `Coordinates`, `DocumentSide`, `EntityLifecycleMixin`, `EventDate`, `FamilyUnion`, `HistoricVariant`, `HistoricalName`, `Legibility`, `Media`, `NameBase`, `NameLifecycleMixin`, `NamePerson`, `NameThing`, `Note`, `RecordMetadata`, `RegistryEnvelope`, `SourceRecord`, `SourceReference`, `TextQuality`, `TimePeriod`, `Tombstone`, `Transcript`, `is_tombstoned`, `stamp_tombstone`.

---
Generated dynamically by `src/system/gen_readme/gen_readme.py`.
