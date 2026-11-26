<!--Path: tests/test_gda/test_core/README.md-->
# GDA Core Test Suite (`tests/test_gda/test_core`)

## Purpose
Verifies `gda.core` modules with hermetic unit, regression, contract, and property-based tests. Keeps tests isolated from live external databases and network services.

## Quality Gate
- **Target Coverage:** 100.00% statement and branch coverage for `gda.core`.
- **Static Checks:** `ruff check`, `ruff format --check`, and `mypy` pass with zero errors.
- **Test Runner:** `pytest` with `@hypothesis/given` strategies in `strategies.py`.

## Layout & Fixtures
- `conftest.py`: Shared fixtures for TOML configs, log records, errors, and sample introspectable classes.
- `strategies.py`: Custom Hypothesis strategies for dates, timestamps, ints, floats, and enum tokens.
- `test_core_contract.py`: Locks down `gda.core.__all__` exports and public signatures.
- `test_core_config_1_2_3.py` & `test_core_config_4_5_6.py`: Tests `DatabaseConfig`, `LoggingConfig`, and `AppConfig`.
- `test_core_dates.py`, `test_core_errors.py`, and `test_core_hashes.py`: Module-level unit and regression tests.
- `test_core_logging_formatters.py` & `test_core_logging_logger.py`: Tests `JsonFormatter`, `ConsoleFormatter`, and `GDALogger` lifecycle/sinks.
- `test_core_types_regexes.py` & `test_core_types_guards.py`: Tests regex registries, `MappingProxyType` immutability, and numeric type guards.
- `test_core_introspectable.py` & `test_core_interoperability.py`: Tests `IntrospectableMixin` and cross-module core flows.
- `test_constants/`: Tests `gda.core.constants` facade exports, domain bounds, military sets, and census sets.
- `test_enums/`: Per-domain enum tests, coercion tests (`test_enums_coercion.py`), and enum contract tests (`test_enums_contract.py`).