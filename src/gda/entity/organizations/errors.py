"""Path: src/gda/entity/organizations/errors.py

Domain-specific exception hierarchy for organization entity management.

Operational Role:
    Defines specialized exceptions for missing organization records,
    institutional hierarchy violations, and structural validation failures,
    inheriting directly from GenealogyDeskError.
"""

from __future__ import annotations

from typing import Any

from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.1"

__all__ = [
    "OrganizationError",
    "OrganizationHierarchyError",
    "OrganizationNotFoundError",
    "OrganizationValidationError",
]


class OrganizationError(GenealogyDeskError):
    """Base exception for all organization domain errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_ORG",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize organization base error."""
        super().__init__(message, error_code=error_code, details=details)


class OrganizationNotFoundError(OrganizationError):
    """Raised when a requested organization cannot be found or is tombstoned."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_ORG_NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize organization not found error."""
        super().__init__(message, error_code=error_code, details=details)


class OrganizationHierarchyError(OrganizationError):
    """Raised when an organization parent/child hierarchy or retirement violates graph rules."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_ORG_HIERARCHY",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize organization hierarchy error."""
        super().__init__(message, error_code=error_code, details=details)


class OrganizationValidationError(OrganizationError):
    """Raised when an organization fails URN, naming, or foreign key validation."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_ORG_VALIDATION",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize organization validation error."""
        super().__init__(message, error_code=error_code, details=details)
