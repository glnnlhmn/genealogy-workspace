# Name: errors.py
# Path: src/gda/core/errors.py
# Version: 1.0.0+build.r7

"""Exception hierarchy and error contracts for GDA Core.

Operational Role:
    Defines the root exception tree, structured error details serialization,
    and diagnostic error codes across domain validation, configuration parsing,
    and runtime subsystem boundaries.

Classes:
    GenealogyDeskError: Canonical base exception with structured error metadata.
    ConfigError: Root exception for configuration-layer failures.
    ConfigValidationError: Raised when configuration payloads violate constraints.
    ConfigParseError: Raised when configuration file formats or TOML syntax fail.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

__version__ = "1.0.0+build.r7"


class GenealogyDeskError(Exception):
    """Canonical base exception for all Genealogy Digital Archive components.

    Attributes:
        message: Human-readable error diagnostic message.
        error_code: Standardized system error code string.
        details: Structured dictionary carrying contextual diagnostic state.
        timestamp: ISO 8601 UTC timestamp string ending with Z.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_GENERIC",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize GenealogyDeskError.

        Args:
            message: Human-readable diagnostic description of the failure.
            error_code: Canonical uppercase error identifier.
            details: Optional dictionary of contextual diagnostic attributes.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def __str__(self) -> str:
        """Render string representation matching standard exception message."""
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception metadata into structured JSON-compatible payload.

        Returns:
            Dictionary containing error_code, message, details, and timestamp.
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class ConfigError(GenealogyDeskError):
    """Root exception for configuration load, validation, and parsing defects."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_CONFIG",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ConfigError."""
        super().__init__(message, error_code=error_code, details=details)


class ConfigValidationError(ConfigError):
    """Raised when configuration values violate data types or domain bounds."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_CONFIG_VALIDATION",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ConfigValidationError."""
        super().__init__(message, error_code=error_code, details=details)


class ConfigParseError(ConfigError):
    """Raised when configuration files cannot be located, decoded, or parsed."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_CONFIG_PARSE",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ConfigParseError."""
        super().__init__(message, error_code=error_code, details=details)
