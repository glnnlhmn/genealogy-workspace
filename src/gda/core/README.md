# Core Primitives & Introspection (src/gda/core)

## Architectural Role
Domain-agnostic foundational infrastructure providing canonical error taxonomies, immutable Pydantic configuration, structured logging, and runtime class introspection.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_core/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `config.py` | `1.0.0+build.r7` | Multi-tiered configuration engine for GDA Core components. |
| `errors.py` | `1.0.0+build.8` | Exception hierarchy and error contracts for GDA Core. |
| `introspectable.py` | `1.0.0+build.r4` | Provide centralized runtime introspection mixin for self-documenting archive components. |
| `logging.py` | `1.0.0+build.r6` | Structured JSON and console logging subsystem for GDA Core. |

## Public Exports & Consumption Contract
Exports: `AppConfig`, `ConfigError`, `ConfigParseError`, `ConfigValidationError`, `ConsoleFormatter`, `DatabaseConfig`, `GDALogger`, `GenealogyDeskError`, `IntrospectableMixin`, `JsonFormatter`, `LoggingConfig`.

---
Generated dynamically by `src/system/generate_readmes.py`.
