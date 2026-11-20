<!--Path: src/gda/model/atom/README.md-->
# Atomic Value Objects & Identifiers (src/gda/model/atom)

## Architectural Role
Immutable Tier-0 atomic value objects enforcing strict domain constraints: 6-digit prefixed entity identifiers, RFC 4122 UUIDv4 strings, calendar dates, UTC timestamps, coordinates, scalars, and archival URNs.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_atom/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `date.py` | `1.0.0+build.5` | Atomic temporal value primitives for calendar dates and UTC timestamps. |
| `gender.py` | `1.0.0+build.7` | Biological sex and gender at birth atomic value object representation. |
| `geo.py` | `1.0.0+build.9` | Geographic coordinate scalar primitives using Pydantic dataclasses. |
| `id.py` | `1.0.0+build.5` | Canonical domain entity identifier primitives using Pydantic dataclasses. |
| `scalar.py` | `1.0.0+build.8` | Domain scalar metrics and code primitives using Pydantic dataclasses. |
| `urn.py` | `1.0.0+build.3` | Archival Uniform Resource Name (URN) atomic primitives using Pydantic dataclasses. |
| `year.py` | `1.0.0+build.5` | Core atomic calendar year primitives and lifecycle year subclasses. |

## Public Exports & Consumption Contract
Exports: `AhnentafelNumber`, `ArchivalURN`, `AtomID`, `BirthYear`, `CemeteryPlotUrn`, `CensusUrn`, `ConfidenceScore`, `DateString`, `DeathYear`, `DraftRecordID`, `FactID`, `FamilyID`, `GenderAtom`, `HistoricalYear`, `IndividualID`, `IsoTimestamp`, `Latitude`, `LocationID`, `Longitude`, `MediaID`, `MilitaryDraftUrn`, `NewsCategoryCode`, `NoteID`, `OrganizationID`, `PubCode`, `QuayScore`, `RepositoryID`, `ServiceRecordID`, `SiteID`, `SourceID`, `SourceURN`, `TranscriptID`, `UUIDv4Str`, `VitalCertificateUrn`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: fe9617f414224a8f -->
