<!--
Name: adr_001_core_realignment.md
Path: docs/architecture/adr_001_core_realignment.md
Version: 1.0.0+build.r1
-->

# ADR 001: Architectural Realignment of `gda.core` Foundation

## Status
Accepted / Implemented (2026-10-15)

## Context
The original topic specification (`prompts/topics/topic_library_architecture.md`) designated `tools/lib/gdacore/` as a monolithic infrastructure module containing runtime configuration, bracketed logging, atomic Safe Backups, JSON utilities, URN reference management, and controlled vocabulary token validation.

During implementation, this design created circular dependencies, conflated pure primitives with disk I/O mutations, and introduced domain-specific genealogical logic into the core package.

## Decision
We realigned `gda.core` to adhere to the following invariants:
1. **Top-Level Package Namespace:** Relocated from `tools/lib/gdacore/src/gdacore/` to `src/gda/core/`.
2. **Pure In-Memory Primitives:** `gda.core` contains zero domain logic and zero filesystem mutation logic. It is strictly scoped to:
   - `errors.py`: Canonical exception tree (`GenealogyDeskError`, `ConfigError`, `ConfigValidationError`, `ConfigParseError`).
   - `config.py`: Immutable Pydantic v2 configuration models (`AppConfig`, `DatabaseConfig`, `LoggingConfig`) with multi-tier precedence loading.
   - `logging.py`: Dual-pipeline structured JSON file logger and bracketed terminal logger.
   - `introspectable.py`: Runtime reflection engine via `_HybridHelpDescriptor` and `IntrospectableMixin`.
3. **Decoupling Filesystem Operations:** `util.py` and `fs.py` were eliminated from `core`. Atomic write staging, Safe Backup protocol (`backups/[file].[timestamp].bk`), and JSON disk serialization are assigned to the incoming `gda.io` package.
4. **Relocating Domain Managers:** `reference_manager` (URN parsing) and `vocabulary_manager` (controlled vocabulary taxonomies) are moved from `core` to `gda.model` / `gda.schema`.
5. **Quality Gate:** 100% statement and branch test coverage enforced across all modules, verified with Ruff compliance.