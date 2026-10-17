# Name: errors.py
# Path: src/gda/model/atom/errors.py

"""Domain error hierarchy for atomic primitive validation failures.

Operational Role:
    Defines specialized exceptions raised by atomic data types (dates,
    identifiers, scalars, coordinates) across the Genealogy Digital
    Archive (GDA). Inherits directly from the core GenealogyDeskError.

Architecture:
    - AtomError: Root exception for all atomic validation failures.
    - AtomFormatError: Raised when format or pattern matching fails.
    - AtomRangeError: Raised when numerical or temporal boundaries are exceeded.
    - AtomPrefixMismatchError: Raised when entity ID prefixes fail expectations.
"""

from __future__ import annotations

from typing import Any

from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.r4"


class AtomError(GenealogyDeskError):
    """Base exception for all atomic primitive validation errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_ATOM_VALIDATION",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, details=details)


class AtomFormatError(AtomError):
    """Raised when an atomic primitive string violates structural syntax."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_ATOM_FORMAT",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, details=details)


class AtomRangeError(AtomError):
    """Raised when an atomic numerical or temporal value exceeds bounded limits."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_ATOM_RANGE",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, details=details)


class AtomPrefixMismatchError(AtomError):
    """Raised when an AtomID string contains a prefix conflicting with its type."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_ATOM_PREFIX_MISMATCH",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, details=details)
