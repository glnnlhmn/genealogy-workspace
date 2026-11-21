<!--Path: .skills/gda-library/SKILL.md-->
---
name: gda-library
description: Architecture, unidirectional dependency tiers (Tier 0-4), immutability, tombstoning, and introspection contracts for the src/gda/ genealogical domain framework. Use whenever designing, writing, refactoring, or auditing code under src/gda/ or tests/test_gda/.
---

# GDA Library Architecture

Dependency tiers, domain invariants, and behavioral contracts for the core genealogical framework (`src/gda/`).

## When to Use

- Writing, refactoring, or auditing modules under `src/gda/` or `tests/test_gda/`.
- Evaluating cross-package imports and architectural layer boundaries.
- Implementing domain models, entity collections, repositories, or analytical engines.

## Unidirectional Dependency Tiers

Enforce a strict bottom-up dependency hierarchy so imports remain acyclic and domain state stays decoupled from storage. Lower tiers must never import from higher tiers:

1. **Tier 0 - Foundation and Primitives (`gda.core`, `gda.util`, `gda.io`):**
   - `gda.core`: Configuration, canonical error taxonomy, structured logging, `IntrospectableMixin`, and domain enumerations (`gda.core.enums`). Depends only on the Python standard library and Pydantic.
   - `gda.util`: Pure ID, text, date, phonetic, and enum helpers. Depends strictly on `gda.core`.
   - `gda.io`: Physical UTF-8 disk I/O, atomic temporary staging, and pre-write Safe Backups (`archive/backups_<project>/`). Depends strictly on `gda.core`.
2. **Tier 1 - Domain Models (`gda.model`):**
   - Immutable, strictly validated structures across `atom/`, `base/`, `entity/`, `xref/`, and `source/`.
   - Consumes Tier 0 (`gda.core`, `gda.util`). Completely decoupled from physical disk I/O (`gda.io`) and SQLite sessions (`gda.db`).
3. **Tier 2 - Relational Persistence and Entity Collections (`gda.db`, `gda.entity`):**
   - Transactional SQLite sessions, schema migrations, row mappers (`gda.db`), and in-memory entity collections with secondary indexing and validation (`gda.entity`).
   - Consumes Tiers 0 and 1.
4. **Tier 3 - Unified Domain Repositories (`gda.repository`):**
   - Query construction, collection caching, and persistence routing across entity, source, and cross-reference domains.
   - Consumes Tiers 0 through 2.
5. **Tier 4 - Analytical Engines and Managers (`gda.engine`, `gda.manager`):**
   - Graph traversal, kinship inference, biological plausibility checks (`gda.engine`), and vocabulary/reference governance (`gda.manager`).
   - Consumes Tiers 0 through 3; consumed by `src/cli/` and `src/ancestry_desk/`.

## Core Behavioral Contracts

- **Introspection:** Public service classes, domain models, and collection facades inherit `IntrospectableMixin` from `gda.core` to provide uniform `.help()` discovery.
- **Immutability and Copy-on-Write:** Domain models are frozen; state transitions occur via copy-on-write mutators that refresh `AuditStamp` metadata.
- **In-Place Tombstoning:** Deprecated, superseded, or merged records remain in primary stores with tombstone metadata (`is_deprecated`, `superseded_by`) rather than being silently purged.
- **Safe Backups:** All filesystem mutations route through `gda.io` to enforce atomic replacements and pre-write snapshots in `archive/backups_gda/`.
- **Quality Gate:** Maintain co-located tests under `tests/test_gda/` achieving >= 95.00% statement and branch coverage and 0 mypy/Ruff errors.

## Gotchas

- Use the live filesystem tree emitted by `gd-struct` as the authoritative layout reference rather than hardcoded directory trees.
- Never allow `gda.model` to import `gda.io` or `gda.db`.
