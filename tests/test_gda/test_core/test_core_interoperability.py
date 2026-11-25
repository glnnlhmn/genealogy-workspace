"""Path: tests/test_gda/test_core/test_core_interoperability.py

Cross-subsystem interoperability test suite for gda.core primitives.

Operational Role:
    Validates end-to-end interactions across gda.core modules without duplicating
    single-module unit tests: AppConfig-driven GDALogger persistence, structured
    exception serialization in JSON logs, malformed TOML error translation,
    log timestamp/hash verification via dates and hashes utilities, and
    IntrospectableMixin composition with core services.

Test Structure & Protocol:
    - Atomized tests: 1:1 cross-subsystem workflow mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integration).
    - Dependencies: Isolated tmp_path sandboxes with explicit handler teardown.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gda.core import (
    AppConfig,
    ConfigParseError,
    ConfigValidationError,
    GDALogger,
    IntrospectableMixin,
    LoggingConfig,
    is_valid_sha256,
    parse_iso_timestamp,
    sha256_file,
    validate_iso_timestamp,
)

__version__ = "1.0.0+build.10"


def _close_logger(gda_logger: GDALogger) -> None:
    """Close and detach all handlers on a GDALogger to release Windows file locks."""
    for handler in list(gda_logger.logger.handlers):
        handler.close()
        gda_logger.logger.removeHandler(handler)


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single end-to-end smoke gate verifying AppConfig -> GDALogger -> disk.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_app_config_drives_logger_persistence_smoke(tmp_path: Path) -> None:
    """Verify AppConfig loads TOML logging settings and drives GDALogger file output."""
    cfg_file = tmp_path / "gda_config.toml"
    cfg_file.write_text(
        "[logging]\n"
        'level = "DEBUG"\n'
        "log_to_console = false\n"
        "log_to_file = true\n"
        'log_file_path = "runtime/interop.log"\n',
        encoding="utf-8",
    )

    app_cfg = AppConfig.load(config_path=cfg_file)
    logger = GDALogger(name="gda.interop.smoke", config=app_cfg.logging, base_dir=tmp_path)
    try:
        logger.debug("Testing interop trace", details={"module": "test_core"})
    finally:
        _close_logger(logger)

    target_log = tmp_path / "runtime" / "interop.log"
    assert target_log.exists()
    record = json.loads(target_log.read_text(encoding="utf-8").strip())
    assert record["level"] == "DEBUG"
    assert record["message"] == "Testing interop trace"
    assert record["details"] == {"module": "test_core"}


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Cross-module exception translation and structured error log serialization.
# ==============================================================================


@pytest.mark.integration
@pytest.mark.regression
def test_logger_serializes_config_validation_error_structure(tmp_path: Path) -> None:
    """Verify JsonFormatter serializes ConfigValidationError fields and details."""
    log_cfg = LoggingConfig(
        level="INFO",
        log_to_console=False,
        log_to_file=True,
        log_file_path="interop_errors.log",
    )
    logger = GDALogger(name="gda.errors.interop", config=log_cfg, base_dir=tmp_path)
    try:
        try:
            raise ConfigValidationError(
                message="Invalid database port specified",
                error_code="ERR_CFG_INVALID_PORT",
                details={"port": -1, "min": 1, "max": 65535},
            )
        except ConfigValidationError as err:
            logger.error("Configuration failure encountered", exc=err)
    finally:
        _close_logger(logger)

    log_file = tmp_path / "interop_errors.log"
    payload = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert payload["level"] == "ERROR"
    assert payload["message"] == "Configuration failure encountered"
    assert payload["error"]["error_code"] == "ERR_CFG_INVALID_PORT"
    assert payload["error"]["message"] == "Invalid database port specified"
    assert payload["error"]["details"] == {"port": -1, "min": 1, "max": 65535}


@pytest.mark.integration
@pytest.mark.regression
def test_app_config_load_maps_invalid_toml_to_config_parse_error(tmp_path: Path) -> None:
    """Verify AppConfig.load translates TOMLDecodeError into ConfigParseError."""
    bad_toml = tmp_path / "broken.toml"
    bad_toml.write_text("invalid_toml = [unclosed_list\n", encoding="utf-8")

    with pytest.raises(ConfigParseError) as exc_info:
        AppConfig.load(config_path=bad_toml)

    err = exc_info.value
    assert err.error_code == "ERR_CONFIG_TOML_PARSE"
    assert str(bad_toml) in err.message
    assert err.details["path"] == str(bad_toml)


# ==============================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: Multi-module pipelines (logging + dates + hashes) and mixin composition.
# ==============================================================================


@pytest.mark.integration
def test_log_record_timestamp_and_file_digest_interoperate_with_dates_and_hashes(
    tmp_path: Path,
) -> None:
    """Verify emitted log timestamps parse via dates and log files hash via sha256_file."""
    log_cfg = LoggingConfig(
        level="INFO",
        log_to_console=False,
        log_to_file=True,
        log_file_path="audit.log",
    )
    logger = GDALogger(name="gda.audit.interop", config=log_cfg, base_dir=tmp_path)
    try:
        logger.info("Audit event recorded", details={"seq": 1})
    finally:
        _close_logger(logger)

    log_file = tmp_path / "audit.log"
    payload = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert validate_iso_timestamp(payload["timestamp"]) is True
    parsed_dt = parse_iso_timestamp(payload["timestamp"])
    assert parsed_dt.tzinfo is not None

    digest = sha256_file(log_file)
    assert is_valid_sha256(digest) is True


@pytest.mark.integration
def test_introspectable_mixin_composes_with_core_services() -> None:
    """Verify IntrospectableMixin functions when inherited by classes using GDALogger."""

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
    try:
        service = MonitoredService(logger=logger)
        dir_output = service.help(as_str=True)
        assert dir_output is not None
        assert "=== MonitoredService Public Directory ===" in dir_output
        assert "status" in dir_output
        assert "execute_task" in dir_output

        method_output = service.help("execute_task", as_str=True)
        assert method_output is not None
        assert "Help on method 'MonitoredService.execute_task':" in method_output
        assert "task_name" in method_output
        assert "Unique task identifier." in method_output
        assert "True if execution succeeded." in method_output
    finally:
        _close_logger(logger)
