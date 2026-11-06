<!--Path: docs/architecture/specs/task_501_entity_xref_spec.md-->
# Task 501 Architectural Specification & Defensive Test Matrix: EntityXRef & EntityXRefResolver

## 1. Architectural Scope & Operational Invariants
* **Module Targets:** `src/gda/model/xref/entity_xref.py` and `src/gda/model/xref/__init__.py`
* **Test Suite Target:** `tests/test_gda/test_model/test_xref/test_entity_xref.py`
* **Target Coverage Gate:** >= 95.00% statement and branch coverage (100% target)
* **Introspection:** `EntityXRefResolver` inherits `IntrospectableMixin` for interactive `.help()` discovery.
* **Immutability:** `EntityXRef` is a frozen Pydantic dataclass (`ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)`). Queries from `EntityXRefResolver` return immutable tuples to prevent caller-side mutation of internal lookup tables.

## 2. Model & Index Contracts

### 2.1 EntityXRef (Dataclass)
* `xref_id: str`: Deterministic compound primary key: `{subject_id}::{relation_type}::{target_id}[::{role}]`.
* `subject_id: IndividualID | FamilyID`: Originating entity anchor.
* `target_id: IndividualID | FamilyID | FactID | SourceID`: Target entity, event, or evidentiary source.
* `relation_type: str`: Semantic discriminator (`PARTNER`, `CHILD`, `PARENT`, `SUBJECT_FACT`, `PARTICIPANT_FACT`, `CITATION`).
* `role: AssociatedRole | PedigreeType | None`: Relational or secondary participant role.
* `fact_type: FactType | None`: Authoritative event classification if linking facts.
* `temporal_year: int | None`: Extracted four-digit lower-bound year for chronological sorting.
* `quay: QuayScore | None`: Evidentiary certainty rating for cited edges.
* `display_label: str | None`: Human-readable summary label for direct LLM/analytical reasoning.
* `audit: AuditStamp`: Creation and modification timestamps.

### 2.2 EntityXRefResolver (Service Class)
* **Index-Level Change Detection:** Maintains a compilation audit stamp (`last_compiled: AuditStamp`) tracking the overall index state.
* **Bidirectional Mappings:**
  * Individual <-> Families as Partner (`_ind_to_fam_partner`)
  * Individual <-> Families as Child (`_ind_to_fam_child`)
  * Family <-> Children with Pedigree (`_fam_to_children`)
  * Entity <-> Primary Facts (`_entity_to_primary_facts`)
  * Individual <-> Participant Facts with Roles (`_ind_to_participant_facts`)
  * Fact <-> All Linked Entities (`_fact_to_entities`)
  * Target <-> Evidentiary Citations (`_target_to_citations`)
* **Construction & Lifecycle:**
  * `from_collections(individuals, families, facts)`: Bulk hydration from entity lists/iterables.
  * `from_xrefs(xrefs)`: Bulk hydration from serialized edge lists.
  * `index_individual(ind)`, `index_family(fam)`, `index_fact(fact)`: Real-time incremental additions.
  * `evict_entity(entity_id)`: Complete in-place removal of all edges referencing a deprecated or mutated entity.

---

## 3. Comprehensive Test Matrix (30 Atomized Test Cases)

### GROUP 1: EntityXRef Dataclass & Key Generation (Unit)
* `test_entity_xref_instantiation_valid_frozen`: Verify frozen immutability and attribute preservation. (`@pytest.mark.unit`)
* `test_create_key_standard_edge_success`: Verify compound key `{subject}::{rel}::{target}` generation. (`@pytest.mark.unit`)
* `test_create_key_with_associated_role_success`: Verify key formatting when `AssociatedRole` is included. (`@pytest.mark.unit`)
* `test_create_key_with_pedigree_type_success`: Verify key formatting when `PedigreeType` is included. (`@pytest.mark.unit`)
* `test_entity_xref_extra_attribute_rejected`: Verify Pydantic rejects undeclared extra fields. (`@pytest.mark.regression`)
* `test_entity_xref_whitespace_stripped`: Verify string attributes strip leading/trailing whitespace automatically. (`@pytest.mark.unit`)

### GROUP 2: Bulk Hydration & Change Detection (Unit & Smoke)
* `test_resolver_init_empty_state`: Verify clean initialization and valid `last_compiled` timestamp. (`@pytest.mark.unit`)
* `test_resolver_introspectable_help`: Verify `.help()` returns valid Markdown introspection docs. (`@pytest.mark.unit`)
* `test_from_collections_smoke`: Verify complete bulk ingestion from collections of Individual, Family, and Fact entities. (`@pytest.mark.smoke`)
* `test_from_xrefs_bulk_hydration`: Verify direct index construction from an iterable of pre-formed `EntityXRef` edges. (`@pytest.mark.unit`)
* `test_export_xrefs_matches_indexed_edges`: Verify exporting edges yields a comprehensive, deduplicated list. (`@pytest.mark.unit`)
* `test_index_recompilation_updates_timestamp`: Verify adding entities updates the resolver compilation stamp. (`@pytest.mark.unit`)

### GROUP 3: Person & Family Bidirectional Traversal (Unit)
* `test_get_families_as_partner`: Verify querying families where an individual is a registered spouse/partner. (`@pytest.mark.unit`)
* `test_get_families_as_child`: Verify querying families where an individual is registered as a child. (`@pytest.mark.unit`)
* `test_get_spouses_bidirectional`: Verify traversing all co-partners linked through shared family units. (`@pytest.mark.unit`)
* `test_get_children_from_individual`: Verify retrieving all children linked to an individual across multiple families. (`@pytest.mark.unit`)
* `test_get_parents_from_child`: Verify retrieving all parental partners for an individual child. (`@pytest.mark.unit`)
* `test_get_pedigree_for_child`: Verify distinguishing biological vs. adopted/step child linkages. (`@pytest.mark.unit`)

### GROUP 4: Fact & Evidentiary Citations (Unit)
* `test_get_facts_for_subject_all`: Verify retrieving all facts where an entity is the primary subject. (`@pytest.mark.unit`)
* `test_get_facts_for_subject_filtered_by_type`: Verify filtering facts by specific `FactType` (e.g., `BIRTH`). (`@pytest.mark.unit`)
* `test_get_facts_as_participant_all`: Verify retrieving facts where an individual is a secondary participant. (`@pytest.mark.unit`)
* `test_get_facts_as_participant_filtered_by_role`: Verify filtering participant facts by `AssociatedRole` (e.g., `WITNESS`). (`@pytest.mark.unit`)
* `test_get_all_associated_people_for_fact`: Verify returning both primary subject and participants for a given `FactID`. (`@pytest.mark.unit`)
* `test_get_citations_for_fact`: Verify retrieving `SourceID` citations attached to a fact. (`@pytest.mark.unit`)

### GROUP 5: Real-Time Mutation, Idempotency & Eviction (Unit & Regression)
* `test_index_individual_incremental`: Verify dynamically adding an individual creates birth/death fact anchors. (`@pytest.mark.unit`)
* `test_index_family_incremental`: Verify dynamically adding a family updates parent-child mappings in place. (`@pytest.mark.unit`)
* `test_index_fact_incremental`: Verify dynamically adding a fact updates subject, participant, and citation maps. (`@pytest.mark.unit`)
* `test_index_duplicate_entity_idempotent`: Verify re-indexing the exact same entity does not duplicate edges or keys. (`@pytest.mark.regression`)
* `test_evict_entity_removes_all_referencing_edges`: Verify evicting an entity completely purges all associated cross-references. (`@pytest.mark.regression`)
* `test_evict_nonexistent_entity_silent_noop`: Verify evicting an unknown ID executes safely without throwing exceptions. (`@pytest.mark.regression`)