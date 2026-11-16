<!--Path: prompts/tasks/modernization_initiation.md-->
# Task Initialization: Domain Model Modernization, DB Mapping & Intake Pipeline

## 1. Executive Context & Operational Baseline
* **Workspace Anchor:** `G:/My Drive/genealogy-workspace`
* **Python Runtime:** 3.13 (`.venv/`), managed via Ruff (100 char limit) and Pytest (`--strict-markers`, `--basetemp=gtemp/pytest_tmp/`)
* **Branch:** `jean-valjean` (clean working tree, pushed to GitHub)
* **Completed Infrastructure:** 
  - Tier 1 Civil & Spatial ingestion complete: 244 Locations and 64 Sites persisted into `data/db/gen_desk_dev.sqlite`.
  - Canonical layout established: Schemas under `schemas/intake/dev/`, baseline setup data under `data/setup/dev/{locations,sites}/`, and runtime queues under `data/intake/dev/`.
  - CLI orchestrator operational: `src/cli/commands/load_setup.py` (PEP 440 `1.0.0+build.1`) verified with 100% test pass rate.

## 2. Core Problem Statement & Modernization Mandate
Before we can ingest Individuals (`IND-######`), Families (`FAM-######`), Sources (`SRC-######`), and Facts (`FCT-######`), we must modernize the foundation across three tightly coupled tiers:
1. **Base Domain Models (`src/gda/model/`):** Refactor legacy atomic value objects (`atom/`), composite primitives/citations/auditing (`base/`), and domain entity classes (`entity/`) to modern Pydantic v2 / Python 3.13 semantics with strict typing and serialization contracts.
2. **Database Mapper / Schema Engine (`src/gda/db/` or `src/gda/entity/`):** Update SQLite table schemas, foreign key cascade behaviors, and CRUD mapping adapters so Python domain dataclasses map 1:1 to database tables without silent type degradation.
3. **Canonical Intake Schemas (`schemas/intake/dev/`):** Modernize JSON schemas (`individual_import.schema.json`, `family_import.schema.json`, `sources_import.schema.json`, and `facts_import.schema.json`) to enforce Draft 2020-12 standards, exact envelope envelopes (`schema_version`, `record_type`, `created_at`, `total_count`), and required properties matching the updated domain models.

## 3. Immediate Phased Roadmap
* **Phase A: Domain Model Modernization (`src/gda/model/`)**
  - Modernize `gda.model.atom` (IDs: `IND-`, `FAM-`, `SRC-`, `FCT-`; dates: `DateString`, `EventDate`).
  - Modernize `gda.model.base` (Onomastic names, historical variants, address/coordinates, audit stamps).
  - Modernize primary entities: `Individual`, `Family`, `Source`, `Fact`.
  - Accompany each module with 1:1 test suites under `tests/test_gda/` (>= 95.00% branch/statement coverage).
* **Phase B: Database Schema & Session Mapper Alignment**
  - Ensure SQLite DDL table definitions support all fields, foreign keys, and indexes for `individuals`, `families`, `sources`, and `facts`.
  - Validate transaction isolation and WAL concurrency in `DatabaseSessionManager`.
* **Phase C: JSON Intake Schemas & Validation**
  - Author/update Draft 2020-12 schemas under `schemas/intake/dev/`.
  - Build validation tests ensuring synthetic partition fixtures parse cleanly against both JSON schemas and Pydantic models.
* **Phase D: Baseline Setup Partitions & CLI Expansion**
  - Extend `src/cli/commands/load_setup.py` to support `--entity {locations,sites,individuals,families,sources,facts,all}`.

## 4. Delivery Directives
* Follow MIP v1.1.4 conventions:
  - Line 1 single-field `Path: [relative/path]` in module docstrings.
  - Native file deliverables only (no string-wrapper scripts).
  - Ruff-compliant syntax (100 char width, sorted imports).
  - Test suites partitioned under `tests/` with registered markers (`unit`, `regression`, `integration`, `integrity`, `smoke`).
  - Safe Backup generation via GSI (`gsi`) before touching existing files.

Let's begin with **Phase A (Step 1): Audit and modernize the base model primitives under `src/gda/model/`**. Please inspect the existing entity models and present the modernized atomic and base classes.