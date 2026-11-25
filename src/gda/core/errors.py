"""Path: src/gda/core/errors.py

Structured exception hierarchy and diagnostic serialization for GDA.

Operational Role:
    Defines the Tier 0 root exception (GenealogyDeskError) and cross-cutting
    configuration and model validation exception hierarchies. Every exception
    captures a UTC ISO-8601 timestamp, canonical error_code, CLI exit_code,
    and defensively isolated diagnostic details for structured logging.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from gda.core.types import ISO_TIMESTAMP_FMT

__version__ = "1.0.0+build.14"

__all__ = [
    "ConfigError",
    "ConfigParseError",
    "ConfigValidationError",
    "GenealogyDeskError",
    "ModelError",
    "ModelFormatError",
    "ModelPrefixMismatchError",
    "ModelRangeError",
]


class GenealogyDeskError(Exception):
    """Root exception for all Genealogy Desk Assistant (GDA) domain errors.

    Subclasses override DEFAULT_ERROR_CODE and DEFAULT_EXIT_CODE via ClassVar
    declarations rather than duplicating __init__ boilerplate.
    """

    DEFAULT_ERROR_CODE: ClassVar[str] = "ERR_GENERIC"
    DEFAULT_EXIT_CODE: ClassVar[int] = 1

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        exit_code: int | None = None,
    ) -> None:
        """Initialize a structured GDA exception without raising secondary errors.

        Args:
            message: Human-readable description of the failure.
            error_code: Machine-readable error identifier; defaults to the
                class's DEFAULT_ERROR_CODE when None.
            details: Optional diagnostic key-value mapping; shallow-copied to
                isolate internal error state from caller mutations.
            exit_code: Process exit status code; defaults to the class's
                DEFAULT_EXIT_CODE when None.
        """
        super().__init__(message)
        self.message: str = message
        # Use explicit `is None` checks so callers can pass "" or 0 intentionally.
        self.error_code: str = self.DEFAULT_ERROR_CODE if error_code is None else error_code
        self.details: dict[str, Any] = dict(details) if details is not None else {}
        self.exit_code: int = self.DEFAULT_EXIT_CODE if exit_code is None else exit_code
        self.timestamp: str = datetime.now(UTC).strftime(ISO_TIMESTAMP_FMT)

    def __str__(self) -> str:
        """Return the raw human-readable error message."""
        return self.message

    def __repr__(self) -> str:
        """Return an unambiguous diagnostic representation for logs and test diffs."""
        return (
            f"{type(self).__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"exit_code={self.exit_code!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize error metadata to a dictionary with defensively copied details.

        Returns:
            A 5-key dictionary containing error_code, message, details,
            timestamp, and exit_code.
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": dict(self.details),
            "timestamp": self.timestamp,
            "exit_code": self.exit_code,
        }


# ==============================================================================
# Configuration Exceptions (Exit Code 2)
# ==============================================================================


class ConfigError(GenealogyDeskError):
    """Base exception for configuration loading, parsing, and validation failures."""

    DEFAULT_ERROR_CODE: ClassVar[str] = "ERR_CONFIG"
    DEFAULT_EXIT_CODE: ClassVar[int] = 2


class ConfigValidationError(ConfigError):
    """Raised when loaded configuration violates schema or domain constraints."""

    DEFAULT_ERROR_CODE: ClassVar[str] = "ERR_CONFIG_VALIDATION"


class ConfigParseError(ConfigError):
    """Raised when a configuration file cannot be parsed (e.g., malformed TOML)."""

    DEFAULT_ERROR_CODE: ClassVar[str] = "ERR_CONFIG_PARSE"


# ==============================================================================
# Model Validation Exceptions (Exit Code 3)
# ==============================================================================


class ModelError(GenealogyDeskError):
    """Base exception for domain model validation and invariant violations."""

    DEFAULT_ERROR_CODE: ClassVar[str] = "ERR_MODEL_VALIDATION"
    DEFAULT_EXIT_CODE: ClassVar[int] = 3


class ModelFormatError(ModelError):
    """Raised when a field value fails canonical format or regex validation."""

    DEFAULT_ERROR_CODE: ClassVar[str] = "ERR_MODEL_FORMAT"


class ModelRangeError(ModelError):
    """Raised when a numeric or temporal value falls outside permitted bounds."""

    DEFAULT_ERROR_CODE: ClassVar[str] = "ERR_MODEL_RANGE"


class ModelPrefixMismatchError(ModelError):
    """Raised when an entity identifier prefix does not match its expected type."""

    DEFAULT_ERROR_CODE: ClassVar[str] = "ERR_MODEL_PREFIX_MISMATCH"
