<!--Path: prompts/topics/topic_library_architecture.md-->
# Topic Specification: Library Architecture, Dependency Tiers & Behavioral Contracts
<!-- Version: 1.0.1 -->
<!-- Operational Directive: Ingest this topic specification as a modular overlay extending the active MIP baseline. Do not execute or rewrite without explicit operator command. Confirm processing and state any conflicts. -->

## 1. Architectural Vision & Authoritative Layout Reference

The `src/` tree separates the core genealogical domain framework (`src/gda/`) from presentation surfaces (`src/ancestry_desk/`), command-line orchestrators (`src/cli/`), and workstation developer utilities (`src/system/`).

* **Single Source of Layout Truth:** Rather than hardcoding static directory trees that drift as packages evolve, the live filesystem tree emitted by `GenDeskStructure` (`GenDeskStructureSrcTests.txt`) and validated by `src/system/util/check_structure.py` serves as the authoritative structural inventory.
* **Test Suite Co-location:** Every production subsystem under `src/` is paired with a co-located test hierarchy under `tests/` (`tests/test_gda/`, `tests/test_cli/`, `tests/test_ancestry_desk/`, `tests/test_system/`) governed by `topic_test_harness.md`.

## 2. Unidirectional Dependency Tiers (`src/gda/`)

To guarantee acyclic imports, high testability, and clean separation between domain state and storage mechanisms, packages within `src/gda/` enforce a strict bottom-up dependency hierarchy. Lower tiers must never import from higher tiers:

1. **Tier 0 - Foundation & Primitives (`gda.core`, `gda.util`, `gda.io`):**
   * **Goal:** Provide domain-agnostic configuration, canonical error taxonomy, structured dual-pipeline logging, runtime introspection (`IntrospectableMixin`), domain enumerations (`gda.core.enums`), pure ID/text/enum helpers (`gda.util`), and atomic UTF-8 file I/O with pre-write Safe Backups (`gda.io`).
   * **Boundary Rule:** `gda.core` depends solely on the Python standard library and Pydantic. `gda.util` and `gda.io` depend strictly on `gda.core`. All physical disk reads, atomic temporary staging, and `archive/backups_[project]/` snapshot creation are isolated to `gda.io`.
2. **Tier 1 - Domain Models & Value Contracts (`gda.model`):**
   * **Goal:** Define immutable, strictly validated domain structures across atomic scalars/identifiers (`atom/`), composite building blocks (`base/`), primary domain entities (`entity/`), bidirectional cross-references (`xref/`), and archival source records (`source/`).
   * **Boundary Rule:** Consumes Tier 0 (`gda.core`, `gda.util`). Completely decoupled from physical disk I/O (`gda.io`) and SQLite database sessions (`gda.db`).
3. **Tier 2 - Relational Persistence & In-Memory Entity Collections (`gda.db`, `gda.entity`):**
   * **Goal:** Provide transactional SQLite session management, deterministic schema migrations, and bidirectional row mappers (`gda.db`), alongside active in-memory entity collections, secondary indexing, and domain validation (`gda.entity`).
   * **Boundary Rule:** Consumes Tiers 0 and 1.
4. **Tier 3 - Unified Domain Repositories (`gda.repository`):**
   * **Goal:** Coordinate query construction, collection caching, and persistence routing across entity, source, and cross-reference domains.
   * **Boundary Rule:** Consumes Tiers 0 through 2.
5. **Tier 4 - Analytical Engines & Orchestration Managers (`gda.engine`, `gda.manager`):**
   * **Goal:** Execute higher-order graph traversal, fact/media resolution, kinship inference, biological plausibility checks (`gda.engine`), and vocabulary/reference governance (`gda.manager`).
   * **Boundary Rule:** Consumes Tiers 0 through 3; consumed by external application layers (`src/cli/`, `src/ancestry_desk/`).

## 3. Core Cross-Cutting Behavioral Contracts

### 3.1 Introspection Contract (`IntrospectableMixin`)
Public service classes, domain models, and collection facades across `src/gda/` inherit `IntrospectableMixin` from `gda.core` to provide uniform runtime `.help()` discovery and schema inspection in interactive sessions and CLI tools.

### 3.2 Immutability, Audit Stamps & In-Place Tombstoning
* **Copy-on-Write Mutation:** Domain models enforce frozen immutability; state transitions occur through explicit copy-on-write mutators that refresh `AuditStamp` metadata and mark records dirty for persistence synchronization.
* **In-Place Tombstoning:** Deprecated, superseded, or merged records are never silently purged from primary stores; they retain tombstone metadata (`is_deprecated`, `superseded_by`) so historical citations and cross-references resolve deterministically.

### 3.3 Documentation & Package `README.md` Parity
* **PEP 257 & Google-Style Docstrings:** Every module opens on Line 1 with its `Path:` docstring header, declares a PEP 440 `__version__` build counter and sorted `__all__`, and maintains an approximate 15% to 20% comment-and-docstring-to-SLOC density.
* **Package `README.md` Invariant:** Every package directory maintains an accurate `README.md` synchronized with the actual `.py` modules on disk (`gen_readme.py`).

### 3.4 Verification & Quality Gate Governance
All `src/gda/` packages are verified under `tests/test_gda/` in accordance with `topic_test_harness.md`, enforcing registered pytest marker hygiene, zero `ruff` or `mypy` errors, Grade A cyclomatic complexity averages, and the minimum >= 95.00% statement and branch coverage gate.