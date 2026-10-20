<!--Path: prompts/topics/topic_library_architecture.md-->
# Topic Specification: Library Architecture & Packaging Hierarchy
<!-- Version: 1.0.1 -->
<!-- Operational Directive: Ingest this topic specification as a modular overlay extending the active MIP baseline. Do not execute or rewrite without explicit operator command. Confirm processing and state any conflicts. -->

## 1. Architectural Scope & Directory Hierarchy
Application and library source trees reside under `src/`, modularized into domain libraries, CLI tools, system utilities, and application interfaces:

```text
src/
  ├── ancestry_desk/       # Desktop presentation layer (controllers, state, views, app.py)
  ├── cli/                 # Operational CLI orchestrators (commands, formatters, main.py)
  ├── gda/                 # Core domain framework packages
  │     ├── core/          # Foundation primitives, errors, config, logging, introspection
  │     ├── data/          # Static reference datasets and resources
  │     ├── engine/        # Kinship graph and biological plausibility verification
  │     ├── entity/        # Active domain entity management (person, fact, location, site)
  │     ├── enums/         # Categorical and domain enumerations
  │     ├── io/            # File I/O, atomic commit staging, schemas, backup protocols
  │     ├── manager/       # Vocabulary governance and reference minting engines
  │     ├── model/         # Structural entity definitions, primitives, and base schemas
  │     ├── types/         # Foundational primitive types
  │     └── util/          # Pure helper utilities (date normalization, hashing, phonetic algorithms)
  └── system/              # Workstation utilities, hooks, GSI intake, structure verification
```
* Authoritative Inspection: The live filesystem tree emitted by GenDeskStructure serves as the authoritative layout reference.

* Test Suite Co-location: Corresponding test suites are co-located under tests/ (tests/test_ancestry_desk/, tests/test_cli/, tests/test_gda/, tests/test_system/)

## 2. Library Package Roles & Dependencies

All paths anchor strictly to `G:/My Drive/genealogy-workspace` using forward slashes (`/`). The following enumeration outlines primary architectural directories, core services, and subsystems; it represents key operational components rather than an exhaustive listing of every workspace folder.

### **2.1 Core Infrastructure (gda.core)**
  - **Role:** Domain-agnostic foundational primitives providing canonical error hierarchies (errors.py), immutable Pydantic configuration engines (config.py), dual-pipeline structured JSON/console logging (logging.py), and runtime introspection mixins (introspectable.py).
  - **Persistence Boundary:** All physical disk mutations, atomic temporary write staging, and the Safe Backup Protocol reside in gda.io.
  - **Dependency Invariant:** Zero internal framework dependencies. Imports strictly from the Python standard library and Pydantic.

### **2.2 I/O & Persistence Infrastructure (gda.io)**
  - **Role:** Governs all physical filesystem interaction, UTF-8 file access, atomic temporary file staging, and the automated Safe Backup Protocol before write operations.
- **Safe Backup Store:** Manages snapshot emission into isolated `archive/backups_[project]/` targets.  
- **Dependency Invariant:** Depends strictly on gda.core primitives.

### **2.3 Authoritative Enumerations (gda.enums)**
  - **Role:** Standardized domain classifications, evidentiary confidence metrics (QuayScore), kinship roles, onomastic classifications (NameStatus), and archival categories.
  - **Dependency Invariant:** Zero framework dependencies; inherits from standard library StrEnum and IntEnum.

### **2.4 Model Authority & Domain Entities (gda.model)**
  - **Role:** Central domain authority structured into distinct sub-tiers:
    - **atom/:** Immutable atomic value objects (DateString, EventDate, prefixed FactID, IndividualID, FamilyID, SiteID, LocationID, SourceID).
    - **base/:** Composite building blocks, audit stamps, tombstone records, onomastic names, and citation references.
    - **entity/:** Primary domain entities (Individual, Family, Fact) enforcing relational integrity, temporal bounds, and participant linkages.
    - **xref/:** Bidirectional cross-reference indexers and relationship traversal resolvers.
  - **In-Place Tombstoning:** Deprecated, superseded, or absorbed domain entities remain in their primary stores marked with tombstone metadata (is_deprecated: true, superseded_by: <id>).
  - **Dependency Invariant:** Consumes gda.core and gda.enums. Decoupled from physical I/O mutations.

## 3. Core Architectural Contracts

### 3.1 Introspection Contract (IntrospectableMixin)
All public service classes across framework packages inherit IntrospectableMixin from gda.core to provide self-documenting .help() discovery in interactive sessions and terminal runs.

### 3.2 Docstring Specification (PEP 257 & Google Style)
All classes, methods, and callable functions must strictly adhere to PEP 257 and Google-style docstring conventions. Detailed API contracts, parameter types, and return values are maintained directly in code docstrings.

### 3.3 State Persistence & Safe Backups
* **Atomic Writes:** All filesystem mutations and serialized writes must use gda.io routines to enforce atomic file replacements and pre-write Safe Backups.
* **In-Place Tombstoning:** Deprecated, superseded, or absorbed domain entities and assertions remain in their primary stores marked with tombstone metadata (is_deprecated: true, superseded_by: <id>).

### 3.4 Verification & Quality Gates Governance
All packages and modules under `src/gda/` are tested under `tests/test_gda/` in strict conformance with `topic_test_harness.md`, enforcing registered marker hygiene and the minimum >= 95.00% statement and branch coverage gate.
