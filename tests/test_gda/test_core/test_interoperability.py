# Name: test_interoperability.py
# Path: tests/test_gda/test_core/test_interoperability.py
# Version: 1.0.0+build.r4

"""Integration verification suite for GDA Core component interoperability.

Operational Role:
    Validates cross-module integration across gda.core primitives:
    configuration-driven logger initialization, exception payload capture
    in JSON logging pipelines, validation error mapping during config parsing,
    and introspection mixin discovery across core classes.

Test Structure & Protocol:
    - Atomized tests: 1:1 cross-subsystem workflow and contract mapping.
    - Fully decorated: @pytest.mark.integration and @pytest.mark.smoke applied throughout.
    - Dependencies: Isolated tmp_path sandboxes, zero production disk mutations.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import gda.core
from gda.core import (
    AppConfig,
    ConfigParseError,
    ConfigValidationError,
    GDALogger,
    IntrospectableMixin,
    LoggingConfig,
)

__version__ = "1.0.0+build.r4"

# ==============================================================================
# GROUP 1: PUBLIC EXPORT & IMPORT BOUNDARIES
# Note: Validates clean package exports and absence of circular imports
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_core_package_exports_expected_symbols() -> None:
    """Verify gda.core exports all canonical primitives via __all__."""
    expected_symbols = {
        "AppConfig",
        "ConfigError",
        "ConfigParseError",
        "ConfigValidationError",
        "ConsoleFormatter",
        "DatabaseConfig",
        "GDALogger",
        "GenealogyDeskError",
        "IntrospectableMixin",
        "JsonFormatter",
        "LoggingConfig",
    }
    assert set(gda.core.__all__) == expected_symbols
    for symbol in expected_symbols:
        assert hasattr(gda.core, symbol)


# ==============================================================================
# GROUP 2: CONFIGURATION & LOGGING INTEGRATION
# Note: Validates GDALogger lifecycle governed by AppConfig and LoggingConfig
# ==============================================================================


@pytest.mark.integration
def test_logger_initializes_from_loaded_app_config(tmp_path: Path) -> None:
    """Verify GDALogger configures handlers and paths from AppConfig."""
    toml_content = """
    [logging]
    level = "DEBUG"
    log_to_console = false
    log_to_file = true
    log_file_path = "runtime/interop.log"
    """
    cfg_file = tmp_path / "gda_config.toml"
    cfg_file.write_text(toml_content, encoding="utf-8")

    app_cfg = AppConfig.load(config_path=cfg_file)
    logger = GDALogger(name="gda.interop", config=app_cfg.logging, base_dir=tmp_path)

    logger.debug("Testing interop trace", details={"module": "test_core"})

    target_log = tmp_path / "runtime" / "interop.log"
    assert target_log.exists()

    record = json.loads(target_log.read_text(encoding="utf-8").strip())
    assert record["level"] == "DEBUG"
    assert record["message"] == "Testing interop trace"
    assert record["details"] == {"module": "test_core"}


# ==============================================================================
# GROUP 3: ERROR HIERARCHY & LOGGING INTEGRATION
# Note: Validates structured serialization of GenealogyDeskError via JSON logs
# ==============================================================================


@pytest.mark.integration
def test_logger_serializes_config_validation_error_structure(tmp_path: Path) -> None:
    """Verify JsonFormatter extracts structured details from ConfigValidationError."""
    log_cfg = LoggingConfig(
        level="INFO",
        log_to_console=False,
        log_to_file=True,
        log_file_path="interop_errors.log",
    )
    logger = GDALogger(name="gda.errors.interop", config=log_cfg, base_dir=tmp_path)

    try:
        raise ConfigValidationError(
            message="Invalid database port specified",
            error_code="ERR_CFG_INVALID_PORT",
            details={"port": -1, "min": 1, "max": 65535},
        )
    except ConfigValidationError as err:
        logger.error("Configuration failure encountered", exc=err)

    log_file = tmp_path / "interop_errors.log"
    payload = json.loads(log_file.read_text(encoding="utf-8").strip())

    assert payload["level"] == "ERROR"
    assert payload["message"] == "Configuration failure encountered"
    assert "error" in payload
    assert payload["error"]["error_code"] == "ERR_CFG_INVALID_PORT"
    assert payload["error"]["message"] == "Invalid database port specified"
    assert payload["error"]["details"] == {"port": -1, "min": 1, "max": 65535}


# ==============================================================================
# GROUP 4: CONFIGURATION PARSER & ERROR INTEGRATION
# Note: Validates translation of parse failures into canonical error instances
# ==============================================================================


@pytest.mark.integration
def test_app_config_load_maps_invalid_toml_to_config_parse_error(
    tmp_path: Path,
) -> None:
    """Verify AppConfig.load translates TOMLDecodeError into ConfigParseError."""
    bad_toml = tmp_path / "broken.toml"
    bad_toml.write_text("invalid_toml = [unclosed_list", encoding="utf-8")

    with pytest.raises(ConfigParseError) as exc_info:
        AppConfig.load(config_path=bad_toml)

    err = exc_info.value
    assert err.error_code == "ERR_CONFIG_TOML_PARSE"
    assert str(bad_toml) in err.message
    assert err.details["path"] == str(bad_toml)


# ==============================================================================
# GROUP 5: INTROSPECTION COMPOSITION
# Note: Validates IntrospectableMixin composition on core services
# ==============================================================================


@pytest.mark.integration
def test_introspectable_mixin_composes_with_core_services() -> None:
    """Verify IntrospectableMixin functions when inherited by domain-level classes."""

    class MonitoredService(IntrospectableMixin):
        """A core monitored service utilizing configuration and logging."""

        def __init__(self, logger: GDALogger) -> None:
            """Initialize MonitoredService."""
            self.logger = logger
            self._status = "READY"

        @property
        def status(self) -> str:
            """Return the current service operational status."""
            return self._status

        def execute_task(self, task_name: str) -> bool:
            """Execute a named service task.

            Args:
                task_name: Unique task identifier.

            Returns:
                True if execution succeeded.
            """
            self.logger.info(f"Task executed: {task_name}")
            return True

    cfg = LoggingConfig(log_to_console=False, log_to_file=False)
    logger = GDALogger(name="service.test", config=cfg)
    service = MonitoredService(logger=logger)

    dir_output = service.help(as_str=True)
    assert dir_output is not None
    assert "=== MonitoredService Public Directory ===" in dir_output
    assert "status" in dir_output
    assert "execute_task" in dir_output

    method_output = service.help("execute_task", as_str=True)
    assert method_output is not None
    assert "Help on method 'MonitoredService.execute_task':" in method_output
    assert "execute_task" in method_output
    assert "task_name" in method_output
    assert "Unique task identifier." in method_output
    assert "True if execution succeeded." in method_output
