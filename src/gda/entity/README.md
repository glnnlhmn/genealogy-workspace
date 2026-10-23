<!--Path: src/gda/entity/README.md-->
# Entity Subsystem Package (`src/gda/entity`)

## 1. Architectural Scope & Operational Role
The `src/gda/entity/` package provides high-performance, in-memory collection managers and graph traversal engines for canonical genealogical domain entities (`Location`, `Individual`, `Family`, `Fact`). It implements in-memory index synchronization, multi-tier relationship traversal, and in-place graveyard soft-deletion protocols.

## 2. Public Export & Subsystem Matrix
* **`Locations` (`src/gda/entity/locations.py`):**
  * **Primary Indexing:** O(1) hash resolution via `LocationID`.
  * **Secondary Indexing:** O(1) lookups via normalized canonical URN (`urn:gda:loc:...`).
  * **Graph Traversal:** Bidirectional child-parent hierarchical navigation, root ancestor resolution, and predecessor/successor lineage tracking.
  * **Graveyard Management:** In-place soft-deletion via `TombstoneRecord[LocationID]`, recursive redirection through `superseded_by` pointers, and cycle detection.
  * **Temporal Onomastics:** Date-bounded naming variants resolved via `HistoricalName`, `TimePeriod`, and `EventDate`.

## 3. Consumption Contracts & Import Boundaries
* **Inbound Dependencies:** Consumes `gda.core` (errors, logging, mixins), `gda.enums` (vital, location classifications), and `gda.model` (primitives, atom IDs, base entities).
* **Decoupling:** Decoupled from physical disk mutations and serializations; persistence orchestration is delegated strictly to `gda.io`.

## 4. Test Harness & Coverage Status
* **Test Suite:** Co-located under `tests/test_gda/test_entity/test_locations.py`.
* **Coverage Verification:** 100.00% statement and branch coverage achieved across all test tiers (`unit`, `regression`, `smoke`).