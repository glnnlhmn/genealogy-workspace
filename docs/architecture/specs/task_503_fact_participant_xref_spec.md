<!--Path: docs/architecture/specs/task_503_fact_participant_xref_spec.md-->
# Task 503 Architectural Specification & Defensive Test Matrix: FactParticipantXRef & FactParticipantResolver

## 1. Architectural Scope & Operational Invariants
* **Model Module Target:** `src/gda/model/xref/fact_participant_xref.py` and `src/gda/model/xref/__init__.py`
* **Model Test Suite Target:** `tests/test_gda/test_model/test_xref/test_fact_participant_xref.py`
* **Engine Module Target:** `src/gda/engine/fact_resolver.py` and `src/gda/engine/__init__.py`
* **Engine Test Suite Target:** `tests/test_gda/test_engine/test_fact_resolver.py`
* **Target Coverage Gate:** >= 95.00% statement and branch coverage (100.00% target)
* **Architectural Layering:**
  * `gda.model.xref`: Pure, immutable relational cross-reference edge dataclasses.
  * `gda.engine`: Active in-memory inverted graph indexers and relationship traversal services.
* **Introspection:** `FactParticipantResolver` inherits `IntrospectableMixin` from `gda.core` for interactive `.help()` discovery.
* **Immutability:** `FactParticipantXRef` is a frozen Pydantic dataclass (`ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)`). Query projections from `FactParticipantResolver` return immutable tuples.

## 2. Model & Index Contracts

### 2.1 FactParticipantXRef (Model Dataclass)
* `xref_id: str`: Deterministic compound primary key: `{associated_ind_id}::{role}::{fact_id}`.
* `associated_ind_id: IndividualID`: Secondary participant individual identifier (witness, informant, etc.).
* `fact_id: FactID`: Authoritative domain event assertion identifier.
* `primary_subject_id: IndividualID`: Focal persona owning the assertion.
* `role: AssociatedRole`: Participant classification (e.g., WITNESS, INFORMANT, OFFICIANT, GODPARENT).
* `title: str | None`: Contextual description, event label, or narrative title.
* `event_date: EventDate | None`: Genealogical event date representation for chronological sorting.
* `compiled_at: IsoTimestamp`: Monotonic UTC indexing timestamp for cache invalidation comparison against `fact.audit.updated_at`.

### 2.2 FactParticipantResolver (Engine Service Class)
* **Index-Level Change Detection:** Tracks compilation state via `last_compiled: IsoTimestamp`.
* **Bidirectional Inverted Mappings:**
  * Individual <-> Participant Facts (`_ind_to_facts: dict[IndividualID, set[tuple[FactID, AssociatedRole]]]`)
  * Fact <-> Linked Participants (`_fact_to_participants: dict[FactID, list[tuple[IndividualID, AssociatedRole]]]`)
* **Construction & Lifecycle:**
  * `from_facts(facts)`: Bulk hydration directly from an iterable of `Fact` domain entities.
  * `from_xrefs(xrefs)`: Bulk hydration from an iterable of pre-compiled `FactParticipantXRef` edges.
  * `index_fact(fact)`: Incremental addition indexing all participants of a `Fact`.
  * `add_xref(edge)`: Direct edge addition into internal lookup tables.
  * `evict_individual(individual_id)`: In-place purging of all participation entries for an individual.
  * `evict_fact(fact_id)`: In-place purging of all participant links for a deleted or superseded fact.
* **Bidirectional Traversal Queries:**
  * `get_facts_as_participant(individual_id, role=None) -> tuple[FactID, ...]`: Return sorted tuple of FactIDs where individual participated, optionally filtered by role.
  * `get_participants_for_fact(fact_id) -> tuple[tuple[IndividualID, AssociatedRole], ...]`: Return all participants and roles linked to a fact assertion.
  * `get_roles_for_individual(individual_id) -> tuple[AssociatedRole, ...]`: Return sorted tuple of unique roles an individual has served in across all facts.
  * `export_xrefs() -> list[FactParticipantXRef]`: Export all indexed edges.

---

## 3. Comprehensive Test Matrix

### Subsystem A: Model Test Suite (`test_fact_participant_xref.py`)
* **GROUP 1: Creation & Immutability**
  * `test_fact_participant_xref_instantiation_valid`: Verify construction with all attributes. (`@pytest.mark.unit`)
  * `test_fact_participant_xref_create_key_deterministic`: Verify deterministic compound key generation. (`@pytest.mark.unit`)
  * `test_fact_participant_xref_frozen_immutability`: Verify mutating attributes raises frozen error. (`@pytest.mark.unit`)
* **GROUP 2: Validation Boundaries & Defensive Constraints**
  * `test_fact_participant_xref_whitespace_stripped`: Verify string attributes strip whitespace. (`@pytest.mark.unit`)
  * `test_fact_participant_xref_empty_key_rejected`: Verify whitespace-only key raises `ModelFormatError`. (`@pytest.mark.regression`)
  * `test_fact_participant_xref_extra_fields_forbidden`: Verify Pydantic rejects extra attributes. (`@pytest.mark.regression`)

### Subsystem B: Engine Test Suite (`test_fact_resolver.py`)
* **GROUP 1: Initialization & Hydration Factories**
  * `test_resolver_init_empty`: Verify clean initialization and valid timestamps. (`@pytest.mark.unit`)
  * `test_resolver_introspectable_help`: Verify `.help()` returns Markdown documentation. (`@pytest.mark.unit`)
  * `test_resolver_from_facts_smoke`: Verify bulk ingestion from `Fact` entities. (`@pytest.mark.smoke`)
  * `test_resolver_from_xrefs`: Verify bulk instantiation from `FactParticipantXRef` edges. (`@pytest.mark.unit`)
  * `test_resolver_export_xrefs_parity`: Verify exported edges match internal indexed state. (`@pytest.mark.unit`)
* **GROUP 2: Edge Intake & Bidirectional Query Traversals**
  * `test_get_facts_as_participant_all_and_filtered`: Verify unfiltered and role-filtered lookups. (`@pytest.mark.unit`)
  * `test_get_roles_for_individual`: Verify returning unique roles served across all facts. (`@pytest.mark.unit`)
  * `test_traversal_fallbacks_unlinked`: Verify unindexed entities return empty tuples. (`@pytest.mark.unit`)
  * `test_add_duplicate_xref_idempotent`: Verify duplicate additions are idempotent. (`@pytest.mark.regression`)
* **GROUP 3: Individual & Fact Eviction Invariants**
  * `test_evict_individual_purges_all_references`: Verify evicting an individual cleanses maps. (`@pytest.mark.regression`)
  * `test_evict_fact_purges_all_references`: Verify evicting a fact cleanses participant entries. (`@pytest.mark.regression`)
  * `test_evict_nonexistent_individual_or_fact_noop`: Verify evicting unknown IDs is a safe no-op. (`@pytest.mark.regression`)