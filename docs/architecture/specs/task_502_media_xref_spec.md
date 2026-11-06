<!--Path: docs/architecture/specs/task_502_media_xref_spec.md-->
# Task 502 Architectural Specification & Defensive Test Matrix: MediaXRef & MediaXRefResolver

## 1. Architectural Scope & Operational Invariants
* **Model Module Target:** `src/gda/model/xref/media_xref.py` and `src/gda/model/xref/__init__.py`
* **Model Test Suite Target:** `tests/test_gda/test_model/test_xref/test_media_xref.py`
* **Engine Module Target:** `src/gda/engine/media_resolver.py` and `src/gda/engine/__init__.py`
* **Engine Test Suite Target:** `tests/test_gda/test_engine/test_media_resolver.py`
* **Target Coverage Gate:** >= 95.00% statement and branch coverage (100.00% target)
* **Architectural Layering:**
  * `gda.model.xref`: Pure, immutable relational cross-reference edge dataclasses.
  * `gda.engine`: Active in-memory graph indexers and relationship traversal services.
* **Introspection:** `MediaXRefResolver` inherits `IntrospectableMixin` from `gda.core` for interactive `.help()` discovery.
* **Immutability:** `MediaXRef` is a frozen Pydantic dataclass (`ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)`). Query projections from `MediaXRefResolver` return immutable tuples.

## 2. Model & Index Contracts

### 2.1 MediaXRef (Model Dataclass)
* `xref_id: UUID`: Authoritative unique identifier for the cross-reference record (UUID4 default factory).
* `entity_id: AtomID`: Identifier of the linked domain entity (covers `IndividualID`, `FamilyID`, `FactID`, `SiteID`, `LocationID`, etc., with prefix preserving type identity).
* `media_id: UUID`: Unique identifier of the target digital media asset.
* `caption: str | None`: Contextual description, narrative label, or transcription note.
* `date: EventDate | None`: Single genealogical event date representation for media capture or association.
* `compiled_at: IsoTimestamp`: Edge generation and indexing timestamp.

### 2.2 MediaXRefResolver (Engine Service Class)
* **Index-Level Change Detection:** Tracks compilation state via `last_compiled: IsoTimestamp`.
* **Bidirectional Mappings:**
  * Entity <-> Media Assets (`_entity_to_media: dict[AtomID, set[UUID]]`)
  * Media <-> Linked Entities (`_media_to_entities: dict[UUID, set[AtomID]]`)
* **Construction & Lifecycle:**
  * `from_xrefs(xrefs)`: Bulk hydration from an iterable of pre-compiled `MediaXRef` edges.
  * `add_xref(edge)`: Incremental addition to bidirectional mappings.
  * `evict_entity(entity_id)`: In-place purging of all media associations for a given `AtomID`.
  * `evict_media(media_id)`: In-place purging of all entity bindings for a deleted `media_id`.
* **Bidirectional Traversal Queries:**
  * `get_media_for_entity(entity_id) -> tuple[UUID, ...]`: Return sorted tuple of attached `media_id` UUIDs.
  * `get_entities_for_media(media_id) -> tuple[AtomID, ...]`: Return sorted tuple of all linked entity IDs.
  * `export_xrefs() -> list[MediaXRef]`: Export all indexed edges.

---

## 3. Comprehensive Test Matrix

### Subsystem A: Model Test Suite (`test_media_xref.py`)
* **GROUP 1: MediaXRef Creation & Field Invariants**
  * `test_media_xref_instantiation_valid`: Verify construction with entity, media, caption, date, and UUID generation. (`@pytest.mark.unit`)
  * `test_media_xref_frozen_immutability`: Verify modifying fields raises frozen instance error. (`@pytest.mark.unit`)
  * `test_media_xref_default_uuid_minting`: Verify omitted `xref_id` automatically generates a valid UUID4. (`@pytest.mark.unit`)
* **GROUP 2: Validation Boundaries & Defensive Constraints**
  * `test_media_xref_whitespace_stripped`: Verify string attributes strip leading/trailing whitespace automatically. (`@pytest.mark.unit`)
  * `test_media_xref_extra_fields_forbidden`: Verify Pydantic rejects undeclared extra attributes. (`@pytest.mark.regression`)

### Subsystem B: Engine Test Suite (`test_media_resolver.py`)
* **GROUP 1: Initialization & Hydration Factories**
  * `test_resolver_init_empty`: Verify clean initialization and valid `last_compiled` timestamp. (`@pytest.mark.unit`)
  * `test_resolver_introspectable_help`: Verify `.help()` returns Markdown documentation. (`@pytest.mark.unit`)
  * `test_resolver_from_xrefs_smoke`: Verify bulk instantiation from an iterable of `MediaXRef` edges. (`@pytest.mark.smoke`)
  * `test_resolver_export_xrefs_parity`: Verify exported edges match internal indexed state. (`@pytest.mark.unit`)
* **GROUP 2: Edge Intake & Bidirectional Query Traversals**
  * `test_get_media_for_entity_multiple`: Verify retrieving multiple media assets attached to one entity. (`@pytest.mark.unit`)
  * `test_get_entities_for_media_group_portrait`: Verify retrieving multiple entities linked to one media asset. (`@pytest.mark.unit`)
  * `test_traversal_fallbacks_unlinked`: Verify unindexed entities/media return empty tuples. (`@pytest.mark.unit`)
  * `test_add_duplicate_xref_idempotent`: Verify re-adding an edge with the same `xref_id` is a safe no-op. (`@pytest.mark.regression`)
* **GROUP 3: Entity & Media Eviction Invariants**
  * `test_evict_entity_removes_all_media_links`: Verify evicting an entity purges forward and reverse mappings. (`@pytest.mark.regression`)
  * `test_evict_media_removes_all_entity_bindings`: Verify evicting a media asset purges all entity references. (`@pytest.mark.regression`)
  * `test_evict_nonexistent_entity_or_media_noop`: Verify evicting unknown entity or media IDs is a safe no-op. (`@pytest.mark.regression`)