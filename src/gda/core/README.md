<!--Path: src/gda/core/README.md-->
# Core Infrastructure, Primitives & Introspection (src/gda/core)

## Architectural Role
Domain-agnostic foundational infrastructure providing canonical error taxonomies, immutable Pydantic configuration, ISO temporal/SHA-256 helpers, regex/scalar constants, structured logging, and runtime class introspection.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_core/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[enums/](enums/README.md)**: Authoritative categorical and domain enumerations package for GDA Core.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `config.py` | `1.0.0+build.19` | Multi-tiered configuration engine for GDA Core components. |
| `dates.py` | `1.0.0+build.5` | Temporal parsing, ISO-8601 normalization, and date validation routines. |
| `errors.py` | `1.0.0+build.13` | Exception hierarchy and error contracts for GDA Core. |
| `hashes.py` | `1.0.0+build.1` | Pure stateless hashing utilities and checksum validators. |
| `introspectable.py` | `1.0.0+build.9` | Runtime introspection mixin for self-documenting archive components. |
| `logging.py` | `1.0.0+build.9` | Structured JSON and console logging subsystem for GDA Core. |
| `types.py` | `1.0.0+build.7` | Authoritative regex patterns, format tokens, and primitive scalar definitions. |

## Public Exports & Consumption Contract
Exports: `ATOM_ID_PATTERN`, `ATOM_ID_REGEX`, `AppConfig`, `CENSUS_SHEET_SIDES`, `CIVIL_WAR_DRAFT_YEARS`, `COLONIAL_MILITIA_MAX_YEAR`, `COLONIAL_MILITIA_MIN_YEAR`, `ConfigError`, `ConfigParseError`, `ConfigValidationError`, `ConsoleFormatter`, `DatabaseConfig`, `ENTITY_ID_PATTERNS`, `ENTITY_ID_REGEXES`, `ENTITY_URN_PATTERNS`, `ENTITY_URN_REGEXES`, `ENUM_KEY_SEPARATOR_PATTERN`, `ENUM_KEY_SEPARATOR_REGEX`, `GDALogger`, `GENDER_CODES`, `GenealogyDeskError`, `ISO_DATE_FMT`, `ISO_DATE_PATTERN`, `ISO_DATE_REGEX`, `ISO_MONTH_FMT`, `ISO_TIMESTAMP_FMT`, `ISO_TIMESTAMP_PATTERN`, `ISO_TIMESTAMP_REGEX`, `ISO_YEAR_FMT`, `ImmutableBaseModel`, `IntrospectableMixin`, `JsonFormatter`, `LoggingConfig`, `MAX_BOUNTY_LAND_ACREAGE`, `MAX_CENSUS_LINE_NUMBER`, `MAX_CONFIDENCE_SCORE`, `MAX_ENLISTMENT_TERM_MONTHS`, `MAX_FOREIGN_SERVICE_MONTHS`, `MAX_HEIGHT_INCHES`, `MAX_HISTORICAL_YEAR`, `MAX_LATITUDE`, `MAX_LONGITUDE`, `MAX_MINOR_CHILDREN_COUNT`, `MAX_QUAY_SCORE`, `MAX_VIETNAM_LOTTERY_NUMBER`, `MAX_WEIGHT_LBS`, `MIN_AHNENTAFEL`, `MIN_CONFIDENCE_SCORE`, `MIN_ENLISTMENT_TERM_MONTHS`, `MIN_HEIGHT_INCHES`, `MIN_HISTORICAL_YEAR`, `MIN_LATITUDE`, `MIN_LONGITUDE`, `MIN_QUAY_SCORE`, `MIN_VIETNAM_LOTTERY_NUMBER`, `MIN_WEIGHT_LBS`, `MODERN_SSS_MIN_YEAR`, `ModelError`, `ModelFormatError`, `ModelPrefixMismatchError`, `ModelRangeError`, `NEWS_CATEGORY_PATTERN`, `NEWS_CATEGORY_REGEX`, `PUB_CODE_PATTERN`, `PUB_CODE_REGEX`, `SHA256_PATTERN`, `SHA256_REGEX`, `SQL_IDENTIFIER_PATTERN`, `SQL_IDENTIFIER_REGEX`, `TAX_ASSESSMENT_MIN_YEAR`, `URN_BASE_PATTERN`, `URN_BASE_REGEX`, `URN_PATTERNS`, `URN_REGEXES`, `US_AGRICULTURAL_SCHEDULE_YEARS`, `US_FEDERAL_CENSUS_1850_1870_YEARS`, `US_FEDERAL_CENSUS_1900_1910_YEARS`, `US_FEDERAL_CENSUS_TALLY_YEARS`, `US_FEDERAL_CENSUS_YEARS`, `US_MANUFACTURING_SCHEDULE_YEARS`, `US_MORTALITY_SCHEDULE_YEARS`, `US_SLAVE_SCHEDULE_YEARS`, `US_VETERANS_SCHEDULE_YEAR`, `UUID_V4_PATTERN`, `UUID_V4_REGEX`, `WWII_DRAFT_YEARS`, `WWI_DRAFT_YEARS`, `calculate_age_years`, `enums`, `format_utc_timestamp`, `is_valid_sha256`, `parse_iso_date_parts`, `parse_iso_timestamp`, `sha256_bytes`, `sha256_file`, `sha256_text`, `utc_now_iso`, `utc_today_iso`, `validate_iso_date`, `validate_iso_timestamp`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: b57790007aa1573c -->
