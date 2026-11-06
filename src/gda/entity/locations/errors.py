"""Path: src/gda/entity/locations/errors.py

Subsystem exception hierarchy for the locations domain entity library.

Operational Role:
    Defines specialized exceptions for jurisdictional validation failures,
    unresolvable location lookups, and hierarchy traversal errors, anchoring
    to the canonical GenealogyDeskError base exception.
"""

from __future__ import annotations

from typing import Any

from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.2"

__all__ = [
    "LocationError",
    "LocationHierarchyError",
    "LocationNotFoundError",
]


class LocationError(GenealogyDeskError):
    """Root exception for all location subsystem operations and validation failures."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_LOCATION",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize LocationError."""
        super().__init__(message, error_code=error_code, details=details)


class LocationNotFoundError(LocationError):
    """Raised when a location entity cannot be located by ID, URN, or query key."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_LOCATION_NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize LocationNotFoundError."""
        super().__init__(message, error_code=error_code, details=details)


class LocationHierarchyError(LocationError):
    """Raised when an operation violates jurisdictional tier rules or child dependencies."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_LOCATION_HIERARCHY",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize LocationHierarchyError."""
        super().__init__(message, error_code=error_code, details=details)
