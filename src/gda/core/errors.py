"""Path: src/gda/core/errors.py

Exception hierarchy and error contracts for GDA Core.

Operational Role:
    Defines the root exception tree, structured error details serialization,
    CLI exit code mapping, and diagnostic error codes across domain validation,
    configuration parsing, and runtime subsystem boundaries.

Classes:
    GenealogyDeskError: Canonical base exception with structured error metadata.
    ConfigError: Root exception for configuration-layer failures.
    ConfigValidationError: Raised when configuration payloads violate constraints.
    ConfigParseError: Raised when configuration file formats or TOML syntax fail.
    ModelError: Root base exception for all model validation failures.
    ModelFormatError: Raised when format, pattern, or string syntax fails.
    ModelRangeError: Raised when numerical or temporal boundaries are exceeded.
    ModelPrefixMismatchError: Raised when an identifier prefix conflicts with its type.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from gda.core.types import ISO_TIMESTAMP_FMT

__version__ = "1.0.0+build.13"

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


# ==============================================================================
# SECTION 1: ROOT EXCEPTION CONTRACT
# ==============================================================================


class GenealogyDeskError(Exception):
    """Canonical base exception for all Genealogy Digital Archive components.

    Attributes:
        message: Human-readable error diagnostic message.
        error_code: Standardized system error code string.
        details: Structured dictionary carrying contextual diagnostic state.
        timestamp: ISO 8601 UTC timestamp string ending with Z.
        exit_code: Process exit code mapped for CLI termination.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_GENERIC",
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        """Initialize GenealogyDeskError with diagnostic context and UTC timestamp.

        Args:
            message: Human-readable diagnostic description of the failure.
            error_code: Canonical uppercase error identifier.
            details: Optional dictionary of contextual diagnostic attributes.
            exit_code: Process exit code for CLI application termination.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.exit_code = exit_code
        # Format timestamp using canonical ISO_TIMESTAMP_FMT (%Y-%m-%dT%H:%M:%SZ)
        self.timestamp = datetime.now(UTC).strftime(ISO_TIMESTAMP_FMT)

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception metadata into structured JSON-compatible payload.

        Returns:
            Dictionary containing error_code, message, details, timestamp, and exit_code.
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "exit_code": self.exit_code,
        }


# ==============================================================================
# SECTION 2: CONFIGURATION SUBSYSTEM EXCEPTIONS
# ==============================================================================


class ConfigError(GenealogyDeskError):
    """Root exception for configuration load, validation, and parsing defects."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_CONFIG",
        details: dict[str, Any] | None = None,
        exit_code: int = 2,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details, exit_code=exit_code)


class ConfigValidationError(ConfigError):
    """Raised when configuration values violate data types or domain bounds."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_CONFIG_VALIDATION",
        details: dict[str, Any] | None = None,
        exit_code: int = 2,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details, exit_code=exit_code)


class ConfigParseError(ConfigError):
    """Raised when configuration files cannot be located, decoded, or parsed."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_CONFIG_PARSE",
        details: dict[str, Any] | None = None,
        exit_code: int = 2,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details, exit_code=exit_code)


# ==============================================================================
# SECTION 3: MODEL VALIDATION EXCEPTIONS
# ==============================================================================


class ModelError(GenealogyDeskError):
    """Root base exception for all domain model validation failures."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_MODEL_VALIDATION",
        details: dict[str, Any] | None = None,
        exit_code: int = 3,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details, exit_code=exit_code)


class ModelFormatError(ModelError):
    """Raised when string syntax, regex patterns, or structural formats are violated."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_MODEL_FORMAT",
        details: dict[str, Any] | None = None,
        exit_code: int = 3,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details, exit_code=exit_code)


class ModelRangeError(ModelError):
    """Raised when numerical, scalar, or temporal boundaries are exceeded."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_MODEL_RANGE",
        details: dict[str, Any] | None = None,
        exit_code: int = 3,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details, exit_code=exit_code)


class ModelPrefixMismatchError(ModelError):
    """Raised when an entity identifier prefix does not match the target model class."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_MODEL_PREFIX_MISMATCH",
        details: dict[str, Any] | None = None,
        exit_code: int = 3,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details, exit_code=exit_code)
