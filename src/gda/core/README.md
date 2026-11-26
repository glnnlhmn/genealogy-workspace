<!--Path: src/gda/core/README.md-->
# Core Infrastructure, Primitives & Introspection (src/gda/core)

## Architectural Role
Foundational primitives for GDA Core. Provides errors, config models, date and hash helpers, regexes, logging, and class introspection.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_core/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[constants/](constants/README.md)**: Public facade for centralized GDA domain, military, and census constants.
- **[enums/](enums/README.md)**: Authoritative categorical and domain enumerations package for GDA Core.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `config.py` | `1.0.0+build.22` | Multi-tiered configuration engine for GDA Core components. |
| `dates.py` | `1.0.0+build.7` | Temporal parsing, ISO-8601 normalization, and date validation routines. |
| `errors.py` | `1.0.0+build.14` | Structured exception hierarchy and diagnostic serialization for GDA. |
| `hashes.py` | `1.0.0+build.2` | Stateless SHA-256 cryptographic hashing and digest validation utilities. |
| `introspectable.py` | `1.0.0+build.12` | Runtime introspection mixin for self-documenting archive components. |
| `logging.py` | `1.0.0+build.12` | Structured JSON and console logging subsystem for GDA Core. |
| `types.py` | `1.0.0+build.10` | Authoritative regex patterns, format tokens, and strict numeric type guards. |

## Public Exports & Consumption Contract
Exports: `ATOM_ID_PATTERN`, `ATOM_ID_REGEX`, `AppConfig`, `ConfigError`, `ConfigParseError`, `ConfigValidationError`, `ConsoleFormatter`, `DatabaseConfig`, `ENTITY_ID_PATTERNS`, `ENTITY_ID_REGEXES`, `ENTITY_URN_PATTERNS`, `ENTITY_URN_REGEXES`, `ENUM_KEY_SEPARATOR_PATTERN`, `ENUM_KEY_SEPARATOR_REGEX`, `GDALogger`, `GenealogyDeskError`, `ISO_DATE_FMT`, `ISO_DATE_PATTERN`, `ISO_DATE_REGEX`, `ISO_MONTH_FMT`, `ISO_TIMESTAMP_FMT`, `ISO_TIMESTAMP_PATTERN`, `ISO_TIMESTAMP_REGEX`, `ISO_YEAR_FMT`, `ImmutableBaseModel`, `IntrospectableMixin`, `JsonFormatter`, `LoggingConfig`, `ModelError`, `ModelFormatError`, `ModelPrefixMismatchError`, `ModelRangeError`, `NEWS_CATEGORY_PATTERN`, `NEWS_CATEGORY_REGEX`, `PUB_CODE_PATTERN`, `PUB_CODE_REGEX`, `SHA256_PATTERN`, `SHA256_REGEX`, `SQL_IDENTIFIER_PATTERN`, `SQL_IDENTIFIER_REGEX`, `URN_BASE_PATTERN`, `URN_BASE_REGEX`, `URN_PATTERNS`, `URN_REGEXES`, `UUID_V4_PATTERN`, `UUID_V4_REGEX`, `calculate_age_years`, `constants`, `enums`, `format_utc_timestamp`, `is_finite_number`, `is_strict_int`, `is_valid_sha256`, `parse_iso_date_parts`, `parse_iso_timestamp`, `sha256_bytes`, `sha256_file`, `sha256_text`, `utc_now_iso`, `utc_today_iso`, `validate_iso_date`, `validate_iso_timestamp`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 111b67299b3b2d24 -->
