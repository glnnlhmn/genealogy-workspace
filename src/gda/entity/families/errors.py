"""Path: src/gda/entity/families/errors.py

Domain-specific exception hierarchy for domestic family unit management.

Operational Role:
    Defines specialized exceptions for missing family records and spousal,
    filial, or foreign key validation failures, inheriting directly from
    GenealogyDeskError.
"""

from __future__ import annotations

from typing import Any

from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.1"

__all__ = [
    "FamilyError",
    "FamilyNotFoundError",
    "FamilyValidationError",
]


class FamilyError(GenealogyDeskError):
    """Base exception for all domestic family unit domain errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_FAM",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize family base error."""
        super().__init__(message, error_code=error_code, details=details)


class FamilyNotFoundError(FamilyError):
    """Raised when a requested family unit cannot be found or is tombstoned."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_FAM_NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize family not found error."""
        super().__init__(message, error_code=error_code, details=details)


class FamilyValidationError(FamilyError):
    """Raised when a family unit fails URN, partner, child, or union validation."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_FAM_VALIDATION",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize family validation error."""
        super().__init__(message, error_code=error_code, details=details)
