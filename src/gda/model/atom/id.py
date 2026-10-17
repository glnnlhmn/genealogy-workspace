# Name: id.py
# Path: src/gda/model/atom/id.py

"""Core atomic identifier models and domain subclasses using Pydantic dataclasses.

Operational Role:
    Serves as the foundational, indivisible identification layer ('Atom') for the
    Genealogy Digital Archive (GDA). Isolates generic format validation, string
    normalization, prefix/suffix slicing, total ordering, and RFC 4122 UUIDv4
    verification away from downstream entity models.

Architecture:
    - AtomID: Base Pydantic dataclass validating 'AAA-######' (min 6 digits) with total ordering.
    - Specialized Atom IDs: IndividualID (IND), FactID (FID), LocationID (LOC), SiteID (SID),
      FamilyID (FAM), NoteID (NOT), and RepositoryID (REP).
    - UUIDv4Str: Base Pydantic dataclass validating RFC 4122 lowercase UUIDv4.
    - Specialized UUID IDs: SourceId, MediaId, and TranscriptID.
"""

from __future__ import annotations

import re
from functools import total_ordering
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.errors import AtomFormatError, AtomPrefixMismatchError

__version__ = "1.0.0+build.r6"

_logger = GDALogger(__name__)


# ==============================================================================
# SECTION 1: BASE ATOM IDENTIFIER (AAA-######)
# ==============================================================================


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class AtomID(IntrospectableMixin):
    """Indivisible base identifier validating the generic 'AAA-######' pattern."""

    value: str
    expected_prefix: str | None = Field(default=None, repr=False)

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^([A-Z]{3})-(\d{6,})$")
    EXPECTED_PREFIX: ClassVar[str | None] = None

    def __post_init__(self) -> None:
        match = self._PATTERN.match(self.value)
        if not match:
            err_msg = (
                f"Invalid AtomID format: '{self.value}'. "
                "Must match 'AAA-######' (3 uppercase letters, hyphen, 6+ digits)."
            )
            _logger.debug(
                "Identifier syntax validation failed", details={"raw_value": self.value}
            )
            raise AtomFormatError(err_msg, details={"value": self.value})

        parsed_prefix, _ = match.groups()
        target_prefix = (
            self.expected_prefix
            if self.expected_prefix is not None
            else self.EXPECTED_PREFIX
        )

        if target_prefix is not None and parsed_prefix != target_prefix:
            err_msg = (
                f"Prefix mismatch for {self.__class__.__name__}: "
                f"expected prefix '{target_prefix}', got '{parsed_prefix}' in '{self.value}'."
            )
            _logger.debug(
                "Identifier prefix mismatch detected",
                details={
                    "class": self.__class__.__name__,
                    "expected": target_prefix,
                    "actual": parsed_prefix,
                    "value": self.value,
                },
            )
            raise AtomPrefixMismatchError(
                err_msg,
                details={
                    "class": self.__class__.__name__,
                    "expected": target_prefix,
                    "actual": parsed_prefix,
                    "value": self.value,
                },
            )

    @property
    def prefix(self) -> str:
        return self.value.split("-", 1)[0]

    @property
    def suffix(self) -> str:
        return self.value.split("-", 1)[1]

    @property
    def number(self) -> str:
        return self.suffix

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value='{self.value}')"

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, AtomID):
            return self.value < other.value
        if isinstance(other, str):
            return self.value < other
        return NotImplemented


# ==============================================================================
# SECTION 2: SPECIALIZED PREFIX SUBCLASSES
# ==============================================================================


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class IndividualID(AtomID):
    """Canonical identifier for an individual record (prefix 'IND')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "IND"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class FactID(AtomID):
    """Canonical identifier for an assertional fact record (prefix 'FID')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "FID"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class LocationID(AtomID):
    """Canonical identifier for a civil jurisdiction record (prefix 'LOC')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "LOC"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class SiteID(AtomID):
    """Canonical identifier for a physical site or facility (prefix 'SID')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "SID"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class FamilyID(AtomID):
    """Canonical identifier for a nuclear family grouping (prefix 'FAM')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "FAM"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class NoteID(AtomID):
    """Canonical identifier for an archival research note (prefix 'NOT')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "NOT"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class RepositoryID(AtomID):
    """Canonical identifier for a custodial archive or repository (prefix 'REP')."""

    EXPECTED_PREFIX: ClassVar[str | None] = "REP"


# ==============================================================================
# SECTION 3: BASE UUIDV4 IDENTIFIER
# ==============================================================================


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class UUIDv4Str(IntrospectableMixin):
    """Indivisible base identifier validating RFC 4122 lowercase UUIDv4 format."""

    value: str

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    )

    def __post_init__(self) -> None:
        if not self._PATTERN.match(self.value):
            err_msg = (
                f"Invalid UUIDv4 format for {self.__class__.__name__}: '{self.value}'. "
                "Must match RFC 4122 lowercase UUIDv4 format."
            )
            _logger.debug(
                "UUIDv4 syntax validation failed", details={"raw_value": self.value}
            )
            raise AtomFormatError(
                err_msg,
                error_code="ERR_UUID_FORMAT",
                details={"value": self.value, "class": self.__class__.__name__},
            )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value='{self.value}')"

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, UUIDv4Str):
            return self.value < other.value
        if isinstance(other, str):
            return self.value < other
        return NotImplemented


# ==============================================================================
# SECTION 4: SPECIALIZED UUID SUBCLASSES
# ==============================================================================


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class SourceId(UUIDv4Str):
    """Canonical identifier for primary archival source citations."""


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class MediaId(UUIDv4Str):
    """Canonical identifier for digital media attachments and files."""


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class TranscriptID(UUIDv4Str):
    """Canonical identifier for full-text verbatim transcripts."""
