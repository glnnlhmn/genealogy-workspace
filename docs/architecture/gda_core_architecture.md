<!--
Name: gda_core_architecture.md
Path: docs/architecture/gda_core_architecture.md
Version: 1.0.0+build.r1
-->

# Architecture Guide: `gda.core` Foundation

## 1. Overview & Architectural Role
`gda.core` provides the foundational, domain-agnostic primitives across the Genealogy Digital Archive codebase. It contains zero knowledge of genealogical entities, genealogical schemas, or physical disk mutations.

### Module Inventory
* **`gda.core.errors`**: Canonical exception hierarchy and structured error dictionaries.
* **`gda.core.config`**: Multi-tiered Pydantic configuration engine.
* **`gda.core.logging`**: Dual-channel structured JSON and bracketed console logger.
* **`gda.core.introspectable`**: Runtime introspection and interactive `.help()` discovery.

---

## 2. Component Specifications

### 2.1 Error Hierarchy (`errors.py`)
Root base exception `GenealogyDeskError` provides structured diagnostics:
* `error_code`: Standard uppercase identifier string (e.g., `ERR_GENERIC`, `ERR_CONFIG_VALIDATION`).
* `timestamp`: UTC ISO 8601 string formatted with trailing `Z` (e.g., `2026-10-15T18:04:33.189045Z`).
* `details`: Key-value contextual state dictionary.
* `to_dict()`: Canonical dictionary serialization for JSON logging and API responses.
* `__str__()`: Standard exception string returning `self.message`.

### 2.2 Configuration Engine (`config.py`)
Configured using Pydantic v2 models with `frozen=True` and `extra="forbid"`:
* `DatabaseConfig`: Connection pool settings, boundary checks, and masked `connection_string` property.
* `LoggingConfig`: Level normalization (case-insensitive), byte boundaries, and file routing flags.
* `AppConfig`: Master container providing `.load()` with strict precedence:
  1. Runtime overrides dictionary
  2. Environment variables (`GDA_*`) with automatic type coercion
  3. `GDA_CONFIG_PATH` target file
  4. Explicit `config_path` TOML file
  5. Dedicated `gda_config.toml` (if present)
  6. `pyproject.toml` (`[tool.gda]`)
  7. Model defaults

### 2.3 Logging Pipeline (`logging.py`)
Dual-formatter architecture managed by `GDALogger`:
* **File Channel (`JsonFormatter`):** Single-line JSON strings ending without newlines. Automatically extracts structured `details` dictionaries and serializes `GenealogyDeskError` payloads under the top-level `"error"` key.
* **Console Channel (`ConsoleFormatter`):** Bracketed readable output: `[LEVEL] [logger] Message | details={...}`.

### 2.4 Introspection Engine (`introspectable.py`)
* `IntrospectableMixin`: Equips classes with `.help()` runtime discovery.
* `_HybridHelpDescriptor`: Dispatches cleanly whether invoked on an uninstantiated class or live instance.
* Outputs Google-style docstrings, call signatures, and active property values.

---

## 3. Verification & Quality Gates
* **Test Location:** `tests/test_gda/test_core/`
* **Coverage Guarantee:** 100% statement and 100% branch test coverage across all modules.
* **Linter Compliance:** Zero diagnostics under `ruff check`.
* **Execution Command:**
  ```bash
  pytest tests/test_gda/test_core/ -v --cov=src/gda/core --cov-branch --cov-report=term-missing --basetemp=gtemp/pytest_tmp