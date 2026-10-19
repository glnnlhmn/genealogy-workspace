# Composite Base Records (src/gda/model/base)

## Architectural Role
Reusable domain composite building blocks: audit stamps, tombstone records, onomastic personal names, source citations, addresses, and time periods.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_base/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `address.py` | `1.0.0+build.5` | Structured postal address representation using Pydantic dataclasses. |
| `age.py` | `1.0.0+build.3` | Age record representation using Pydantic dataclasses. |
| `association.py` | `1.0.0+build.4` | Associated participant representation using Pydantic dataclasses. |
| `audit.py` | `1.0.0+build.5` | Core audit metadata tracking stamp using Pydantic dataclasses. |
| `entity.py` | `1.0.0+build.2` | Foundational base entity schemas for graph nodes and digital assets. |
| `envelope.py` | `1.0.0+build.3` | Administrative collection envelope using Pydantic dataclasses. |
| `family.py` | `1.0.0+build.1` | Relational value objects representing domestic unions and pedigree linkages. |
| `media.py` | `1.0.0+build.3` | Digital media asset metadata representation using Pydantic dataclasses. |
| `name.py` | `1.0.0+build.2` | Canonical personal, jurisdictional, and historical naming representations. |
| `note.py` | `1.0.0+build.5` | Archival research note representation using Pydantic dataclasses. |
| `record_metadata.py` | `1.0.0+build.3` | Administrative source record metadata header using Pydantic dataclasses. |
| `source_reference.py` | `1.0.0+build.3` | Archival citation and source reference representation using Pydantic dataclasses. |
| `time_period.py` | `1.0.0+build.1` | Temporal bounding primitives for historical entity lifecycles. |
| `tombstone.py` | `1.0.0+build.5` | In-place entity lifecycle and deprecation tombstone using Pydantic dataclasses. |
| `transcript.py` | `1.0.0+build.3` | Full-text transcription and abstract representation using Pydantic dataclasses. |

## Public Exports & Consumption Contract
Exports: `Address`, `Age`, `AssociatedIndividual`, `AssociationRole`, `AuditStamp`, `CanonicalName`, `DocumentSide`, `Legibility`, `Media`, `Note`, `NoteType`, `RecordMetadata`, `RegistryEnvelope`, `SourceReference`, `TextQuality`, `TombstoneRecord`, `Transcript`.

---
Generated dynamically by `src/system/generate_readmes.py`.
