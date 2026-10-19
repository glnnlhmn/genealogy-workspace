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
| `date.py` | `1.0.0+build.6` | Core atomic temporal primitives and historical calendar types using Pydantic dataclasses. |
| `geo.py` | `1.0.0+build.6` | Geographic coordinate primitives using Pydantic dataclasses. |
| `id.py` | `1.0.0+build.8` | Core atomic identifier primitives and domain subclasses using Pydantic dataclasses. |
| `scalar.py` | `1.0.0+build.6` | Domain scalar metrics and code primitives using Pydantic dataclasses. |

## Public Exports & Consumption Contract
Exports: `AhnentafelNumber`, `AtomID`, `BirthYear`, `CensusYear`, `CensusYearEnum`, `ConfidenceScore`, `Coordinates`, `DateModifier`, `DateString`, `DeathYear`, `EventDate`, `EventDateRange`, `FactID`, `FamilyID`, `HistoricalYear`, `IndividualID`, `IsoTimestamp`, `Latitude`, `LocationID`, `Longitude`, `MediaID`, `NewsCategoryCode`, `NoteID`, `PubCode`, `QuayScore`, `RepositoryID`, `SiteID`, `SourceID`, `TranscriptID`, `UUIDv4Str`.

---
Generated dynamically by `src/system/generate_readmes.py`.
