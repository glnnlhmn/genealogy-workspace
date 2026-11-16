"""Path: src/gda/entity/facts/errors.py

Domain-specific exception hierarchy for evidentiary fact entity management.

Operational Role:
    Defines specialized exceptions for missing fact records and structural or
    referential validation failures, inheriting directly from GenealogyDeskError.
"""

from __future__ import annotations

from typing import Any

from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.1"

__all__ = [
    "FactError",
    "FactNotFoundError",
    "FactValidationError",
]


class FactError(GenealogyDeskError):
    """Base exception for all evidentiary fact domain errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_FACT",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize fact base error."""
        super().__init__(message, error_code=error_code, details=details)


class FactNotFoundError(FactError):
    """Raised when a requested fact cannot be found or is tombstoned."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_FACT_NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize fact not found error."""
        super().__init__(message, error_code=error_code, details=details)


class FactValidationError(FactError):
    """Raised when a fact fails URN, subject, participant, or foreign key validation."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_FACT_VALIDATION",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize fact validation error."""
        super().__init__(message, error_code=error_code, details=details)
