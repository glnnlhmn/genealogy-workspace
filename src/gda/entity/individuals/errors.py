"""Path: src/gda/entity/individuals/errors.py

Domain-specific exception hierarchy for individual persona entity management.

Operational Role:
    Defines specialized exceptions for missing individual records and
    onomastic, temporal, or foreign key validation failures, inheriting
    directly from GenealogyDeskError.
"""

from __future__ import annotations

from typing import Any

from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.1"

__all__ = [
    "IndividualError",
    "IndividualNotFoundError",
    "IndividualValidationError",
]


class IndividualError(GenealogyDeskError):
    """Base exception for all individual persona domain errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_IND",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize individual base error."""
        super().__init__(message, error_code=error_code, details=details)


class IndividualNotFoundError(IndividualError):
    """Raised when a requested individual cannot be found or is tombstoned."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_IND_NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize individual not found error."""
        super().__init__(message, error_code=error_code, details=details)


class IndividualValidationError(IndividualError):
    """Raised when an individual fails URN, naming, temporal, or place reference validation."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_IND_VALIDATION",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize individual validation error."""
        super().__init__(message, error_code=error_code, details=details)
