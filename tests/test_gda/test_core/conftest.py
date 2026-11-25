"""Path: tests/test_gda/test_core/conftest.py

Shared pytest fixtures and synthetic baselines for gda.core test suites.

Operational Role:
    Provides centralized, in-memory fixture factories and synthetic entities
    organized by core subsystem: configuration (config.py), logging and error
    payloads (logging.py, errors.py), and runtime introspection entities
    (introspectable.py).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from gda.core.config import AppConfig, DatabaseConfig, LoggingConfig
from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger

__version__ = "1.0.0+build.4"

__all__ = [
    "EmptyEntity",
    "MethodOnlyEntity",
    "PropertyOnlyEntity",
    "SampleEntity",
    "SampleIntrospectableService",
    "UndocumentedEntity",
    "empty_entity_cls",
    "make_log_record",
    "make_toml_file",
    "method_only_cls",
    "property_only_cls",
    "sample_app_config",
    "sample_database_config",
    "sample_entity",
    "sample_entity_cls",
    "sample_genealogy_desk_error",
    "sample_log_record",
    "sample_logging_config",
    "sample_valid_toml_content",
    "undocumented_entity_cls",
]


# ==============================================================================
# SECTION 1: CONFIGURATION FIXTURES (config.py)
# Note: Immutable TOML baselines, config models, and hermetic TOML file factory.
# ==============================================================================


@pytest.fixture(scope="session")
def sample_valid_toml_content() -> str:
    """Return canonical TOML configuration text."""
    return """
app_name = "Custom Archive"
environment = "staging"
debug = true

[database]
db_path = "data/custom.db"
busy_timeout = 8000

[logging]
level = "WARNING"
log_to_console = false
log_to_file = true
log_file_path = "runtime/custom.log"
"""


@pytest.fixture
def sample_database_config() -> DatabaseConfig:
    """Return a default DatabaseConfig instance."""
    return DatabaseConfig()


@pytest.fixture
def sample_logging_config() -> LoggingConfig:
    """Return an in-memory LoggingConfig instance with disk/console output off."""
    return LoggingConfig(
        level="DEBUG",
        log_to_console=False,
        log_to_file=False,
    )


@pytest.fixture
def sample_app_config(gda_sandbox_dir: Path) -> AppConfig:
    """Return an AppConfig instance anchored to the hermetic gda_sandbox_dir."""
    return AppConfig(root_path=gda_sandbox_dir)


@pytest.fixture
def make_toml_file(tmp_path: Path) -> Callable[[str, str], Path]:
    """Return a factory that writes UTF-8 TOML text into tmp_path and returns its Path."""

    def _write(content: str, filename: str = "gda_config.toml") -> Path:
        target = tmp_path / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    return _write


# ==============================================================================
# SECTION 2: LOGGING & ERROR FIXTURES (logging.py, errors.py)
# Note: Baseline LogRecord, customizable LogRecord factory, and canonical error.
# ==============================================================================


@pytest.fixture
def sample_log_record() -> logging.LogRecord:
    """Return a baseline standard library LogRecord instance."""
    return logging.LogRecord(
        name="gda.core.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=100,
        msg="Transaction committed",
        args=(),
        exc_info=None,
    )


@pytest.fixture
def make_log_record() -> Callable[..., logging.LogRecord]:
    """Return a factory for constructing LogRecord instances with optional overrides."""

    def _build(
        *,
        name: str = "gda.core.test",
        level: int = logging.INFO,
        msg: str = "Transaction committed",
        lineno: int = 100,
        exc_info: Any = None,
        details: dict[str, Any] | None = None,
        exc: BaseException | None = None,
    ) -> logging.LogRecord:
        record = logging.LogRecord(
            name=name,
            level=level,
            pathname=__file__,
            lineno=lineno,
            msg=msg,
            args=(),
            exc_info=exc_info,
        )
        if details is not None:
            record.details = details
        if exc is not None:
            record.exc = exc
        return record

    return _build


@pytest.fixture
def sample_genealogy_desk_error() -> GenealogyDeskError:
    """Return a canonical GenealogyDeskError instance."""
    return GenealogyDeskError(
        message="Database lookup failed",
        error_code="ERR_DB_TIMEOUT",
        details={"host": "10.0.0.1", "port": 5432},
    )


# ==============================================================================
# SECTION 3: INTROSPECTION ENTITIES & FIXTURES (introspectable.py)
# Note: Synthetic IntrospectableMixin classes covering standard and edge cases.
# ==============================================================================


class SampleEntity(IntrospectableMixin):
    """Synthetic entity fixture demonstrating properties and methods for introspection."""

    CLASS_CONSTANT = "plain_non_callable_attribute"

    def __init__(self, name: str = "TestItem", count: int = 10) -> None:
        """Initialize SampleEntity."""
        self._name = name
        self.count = count

    @property
    def display_name(self) -> str:
        """Return the formatted display name for the entity."""
        return f"Entity:{self._name}"

    @property
    def failing_property(self) -> str:
        """Raise an intentional runtime error during property access."""
        raise RuntimeError("Property calculation failed")

    def execute_action(self, action_name: str, force: bool = False) -> bool:
        """Execute a designated action against the entity.

        Args:
            action_name: The name of the action to execute.
            force: If True, bypass safety constraints.

        Returns:
            True if action executed successfully.
        """
        return bool(action_name and force)

    def simple_action(self) -> None:
        """Execute a simple parameterless action."""
        return None

    def _internal_helper(self) -> None:
        """Private helper that should not appear in public directories."""
        return None


class MethodOnlyEntity(IntrospectableMixin):
    """An entity containing only callable methods without properties."""

    def only_method(self) -> str:
        """Execute the lone method."""
        return "ok"


class PropertyOnlyEntity(IntrospectableMixin):
    """An entity containing only properties without methods."""

    @property
    def only_property(self) -> str:
        """Return lone property."""
        return "val"


class EmptyEntity(IntrospectableMixin):
    """An entity exposing neither public properties nor public methods."""

    _private_value = 42


class UndocumentedEntity(IntrospectableMixin):  # noqa: D101
    @property
    def bare_property(self) -> str:  # noqa: D102
        return "bare"

    def bare_method(self) -> str:  # noqa: D102
        return "bare"


class SampleIntrospectableService(IntrospectableMixin):
    """Monitored service fixture utilizing configuration and logging."""

    def __init__(self, logger: GDALogger) -> None:
        """Initialize SampleIntrospectableService."""
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


@pytest.fixture
def sample_entity() -> SampleEntity:
    """Return an instantiated SampleEntity."""
    return SampleEntity()


@pytest.fixture(scope="session")
def sample_entity_cls() -> type[SampleEntity]:
    """Return the SampleEntity class."""
    return SampleEntity


@pytest.fixture(scope="session")
def method_only_cls() -> type[MethodOnlyEntity]:
    """Return the MethodOnlyEntity class."""
    return MethodOnlyEntity


@pytest.fixture(scope="session")
def property_only_cls() -> type[PropertyOnlyEntity]:
    """Return the PropertyOnlyEntity class."""
    return PropertyOnlyEntity


@pytest.fixture(scope="session")
def empty_entity_cls() -> type[EmptyEntity]:
    """Return the EmptyEntity class."""
    return EmptyEntity


@pytest.fixture(scope="session")
def undocumented_entity_cls() -> type[UndocumentedEntity]:
    """Return the UndocumentedEntity class."""
    return UndocumentedEntity
