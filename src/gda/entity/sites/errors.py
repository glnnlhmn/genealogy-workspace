"""Path: src/gda/entity/sites/errors.py

Subsystem exception hierarchy for the sites domain entity library.

Operational Role:
    Defines specialized exceptions for site validation failures,
    unresolvable site lookups, foreign key violations, and lifecycle
    errors, anchoring to the canonical GenealogyDeskError base exception.
"""

from __future__ import annotations

from typing import Any

from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.1"

__all__ = [
    "SiteError",
    "SiteNotFoundError",
    "SiteValidationError",
]


class SiteError(GenealogyDeskError):
    """Root exception for all site subsystem operations and validation failures."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_SITE",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize SiteError."""
        super().__init__(message, error_code=error_code, details=details)


class SiteNotFoundError(SiteError):
    """Raised when a site entity cannot be located by ID, URN, or query key."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_SITE_NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize SiteNotFoundError."""
        super().__init__(message, error_code=error_code, details=details)


class SiteValidationError(SiteError):
    """Raised when a site violates structural, geospatial, or foreign key invariants."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_SITE_VALIDATION",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize SiteValidationError."""
        super().__init__(message, error_code=error_code, details=details)
