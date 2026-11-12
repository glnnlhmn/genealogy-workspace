"""Path: src/gda/model/atom/id.py

Canonical domain entity identifier primitives using Pydantic dataclasses.

Operational Role:
    Defines validated, immutable identifier value objects enforcing the
    'AAA-######' prefixed format (AtomID and specialized entity subclasses)
    and RFC 4122 lowercase UUIDv4 format (UUIDv4Str and specialized subclasses).
    Supports raw string equality and homogeneous total ordering.
"""

from __future__ import annotations

import re
from functools import total_ordering
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError, ModelPrefixMismatchError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ATOM_ID_REGEX, UUID_V4_REGEX

__version__ = "1.0.2+build.3"

__all__ = [
    "AtomID",
    "DraftRecordID",
    "FactID",
    "FamilyID",
    "IndividualID",
    "LocationID",
    "MediaID",
    "NoteID",
    "RepositoryID",
    "ServiceRecordID",
    "SiteID",
    "SourceID",
    "TranscriptID",
    "UUIDv4Str",
]


@total_ordering
@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class AtomID(IntrospectableMixin):
    """Canonical prefixed entity identifier matching 'AAA-######'."""

    value: str = Field(..., description="Prefixed entity identifier (e.g., 'IND-000001').")
    expected_prefix: str | None = Field(
        default=None,
        description="Optional explicit 3-letter prefix override.",
    )

    EXPECTED_PREFIX: ClassVar[str | None] = None
    _PATTERN: ClassVar[re.Pattern[str]] = ATOM_ID_REGEX

    def __post_init__(self) -> None:
        """Validate canonical 'AAA-######' syntax and prefix constraints."""
        if not isinstance(self.value, str) or not self._PATTERN.match(self.value):
            raise ModelFormatError(
                f"Invalid AtomID format: '{self.value}'. Must match '^[A-Z]{{3}}-\\d{{6,}}$'.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

        required = (
            self.expected_prefix if self.expected_prefix is not None else self.EXPECTED_PREFIX
        )
        if required is not None and self.prefix != required:
            raise ModelPrefixMismatchError(
                f"Prefix mismatch for {self.__class__.__name__}: expected '{required}', got '{self.prefix}'.",
                error_code="ERR_MODEL_PREFIX",
                details={"value": self.value, "expected": required, "actual": self.prefix},
            )

    @property
    def prefix(self) -> str:
        """Return 3-character uppercase entity prefix."""
        return self.value.split("-", 1)[0]

    @property
    def suffix(self) -> str:
        """Return zero-padded numeric suffix string."""
        return self.value.split("-", 1)[1]

    @property
    def number(self) -> str:
        """Alias for suffix returning numeric portion of identifier."""
        return self.suffix

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value='{self.value}')"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with the same AtomID class or raw str."""
        if type(other) is type(self):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Enforce homogeneous ordering strictly between instances of the same concrete class."""
        if type(other) is not type(self):
            return NotImplemented
        return self.value < other.value


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class IndividualID(AtomID):
    """Canonical Individual entity identifier ('IND-######')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "IND"


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class FactID(AtomID):
    """Canonical Fact entity identifier ('FID-######')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "FID"


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class LocationID(AtomID):
    """Canonical Location entity identifier ('LOC-######')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "LOC"


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class SiteID(AtomID):
    """Canonical Site entity identifier ('SID-######')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "SID"


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class FamilyID(AtomID):
    """Canonical Family entity identifier ('FAM-######')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "FAM"


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class NoteID(AtomID):
    """Canonical Note entity identifier ('NOT-######')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "NOT"


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class RepositoryID(AtomID):
    """Canonical Repository entity identifier ('REP-######')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "REP"


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class DraftRecordID(AtomID):
    """Canonical Draft Record entity identifier ('DRF-######')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "DRF"


@total_ordering
@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class UUIDv4Str(IntrospectableMixin):
    """RFC 4122 lowercase UUIDv4 string primitive."""

    value: str = Field(..., description="Lowercase RFC 4122 UUIDv4 string.")

    _PATTERN: ClassVar[re.Pattern[str]] = UUID_V4_REGEX

    def __post_init__(self) -> None:
        """Validate strict lowercase RFC 4122 UUIDv4 format."""
        if not isinstance(self.value, str) or not self._PATTERN.match(self.value):
            raise ModelFormatError(
                f"Invalid UUIDv4 format: '{self.value}'. Must match lowercase RFC 4122 UUIDv4.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value='{self.value}')"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with the same UUIDv4Str class or raw str."""
        if type(other) is type(self):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Enforce homogeneous ordering strictly between instances of the same concrete class."""
        if type(other) is not type(self):
            return NotImplemented
        return self.value < other.value


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class SourceID(UUIDv4Str):
    """Canonical Source entity UUIDv4 identifier."""


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class MediaID(UUIDv4Str):
    """Canonical Media asset UUIDv4 identifier."""


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class ServiceRecordID(UUIDv4Str):
    """Canonical Service Record UUIDv4 identifier."""


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class TranscriptID(UUIDv4Str):
    """Canonical Transcript entity UUIDv4 identifier."""
