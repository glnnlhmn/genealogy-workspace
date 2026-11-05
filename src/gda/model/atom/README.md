# Atomic Value Objects (src/gda/model/atom)

## Architectural Role
Immutable atomic value objects enforcing strict domain constraints: prefixed entity identifiers, calendar dates, timestamps, coordinates, and scalars.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_atom/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `date.py` | `1.0.0+build.9` | Core atomic temporal primitives and historical calendar types using Pydantic dataclasses. |
| `gender.py` | `1.0.0+build.1` | Biological sex and gender at birth atomic value object representation. |
| `geo.py` | `1.0.0+build.6` | Geographic coordinate primitives using Pydantic dataclasses. |
| `id.py` | `1.0.0+build.10` | Core atomic identifier primitives and domain subclasses using Pydantic dataclasses. |
| `scalar.py` | `1.0.0+build.6` | Domain scalar metrics and code primitives using Pydantic dataclasses. |
| `urn.py` | `1.0.0+build.1` | Archival Uniform Resource Name (URN) primitives using Pydantic dataclasses. |

## Public Exports & Consumption Contract
Exports: `AhnentafelNumber`, `ArchivalURN`, `AtomID`, `BirthYear`, `CemeteryPlotUrn`, `CensusUrn`, `CensusYear`, `CensusYearEnum`, `ConfidenceScore`, `Coordinates`, `DateModifier`, `DateString`, `DeathYear`, `DraftRecordID`, `EventDate`, `EventDateRange`, `FactID`, `FamilyID`, `HistoricalYear`, `IndividualID`, `IsoTimestamp`, `Latitude`, `LocationID`, `Longitude`, `MediaID`, `MilitaryDraftUrn`, `NewsCategoryCode`, `NoteID`, `PubCode`, `QuayScore`, `RepositoryID`, `SiteID`, `ServiceRecordID`, `SourceID`, `SourceURN`, `TranscriptID`, `UUIDv4Str`, `VitalCertificateUrn`.

---
Generated dynamically by `src/system/gen_readme.py`.
