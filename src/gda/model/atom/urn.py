"""Path: src/gda/model/atom/urn.py

Archival Uniform Resource Name (URN) atomic primitives using Pydantic dataclasses.

Operational Role:
    Defines immutable, regex-validated archival URN primitives (ArchivalURN and
    domain subclasses SourceURN, MilitaryDraftUrn, CensusUrn, VitalCertificateUrn,
    and CemeteryPlotUrn) without silent mutation, supporting raw string equality
    and homogeneous total ordering.
"""

from __future__ import annotations

import re
from functools import total_ordering
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import URN_BASE_REGEX, URN_REGEXES

__version__ = "1.0.1+build.3"

__all__ = [
    "ArchivalURN",
    "CemeteryPlotUrn",
    "CensusUrn",
    "MilitaryDraftUrn",
    "SourceURN",
    "VitalCertificateUrn",
]


@total_ordering
@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class ArchivalURN(IntrospectableMixin):
    """Base archival Uniform Resource Name primitive."""

    value: str = Field(..., description="Canonical archival URN string.")

    EXPECTED_SCHEME: ClassVar[str] = "URN"
    EXPECTED_NID: ClassVar[str | None] = None
    URN_REGEX: ClassVar[re.Pattern[str]] = URN_BASE_REGEX

    def __post_init__(self) -> None:
        """Validate URN scheme, namespace identifier, and structural regex without mutation."""
        if not isinstance(self.value, str) or not self.value or self.value != self.value.strip():
            raise ModelFormatError(
                f"Invalid {self.__class__.__name__} syntax: '{self.value}'.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

        segments = self.value.split(":")
        if len(segments) >= 1 and segments[0] != self.EXPECTED_SCHEME:
            raise ModelFormatError(
                f"Invalid URN scheme '{segments[0]}' for {self.__class__.__name__}: expected '{self.EXPECTED_SCHEME}'.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value, "scheme": segments[0]},
            )

        if (
            self.EXPECTED_NID is not None
            and len(segments) >= 2
            and segments[1] != self.EXPECTED_NID
        ):
            raise ModelFormatError(
                f"Invalid URN namespace '{segments[1]}' for {self.__class__.__name__}: expected '{self.EXPECTED_NID}'.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value, "nid": segments[1]},
            )

        if not self.URN_REGEX.match(self.value):
            raise ModelFormatError(
                f"Invalid {self.__class__.__name__} syntax: '{self.value}'.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

    @property
    def parts(self) -> list[str]:
        """Return colon-delimited URN segments."""
        return self.value.split(":")

    @property
    def nid(self) -> str:
        """Return Namespace Identifier (second URN segment)."""
        return self.parts[1]

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value='{self.value}')"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with the same URN class or raw str."""
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
class SourceURN(ArchivalURN):
    """Canonical Source URN ('URN:SRC:<YEAR>:<JURISDICTION>:<LOCATOR>')."""

    EXPECTED_NID: ClassVar[str | None] = "SRC"
    URN_REGEX: ClassVar[re.Pattern[str]] = URN_REGEXES["SRC"]

    @property
    def year(self) -> int:
        return int(self.parts[2])

    @property
    def jurisdiction(self) -> str:
        return self.parts[3]

    @property
    def locator(self) -> str:
        return self.parts[4]


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class MilitaryDraftUrn(ArchivalURN):
    """Canonical Military Draft URN ('URN:DRAFT:<YEAR>:<JURISDICTION>:<CARD_LOCATOR>')."""

    EXPECTED_NID: ClassVar[str | None] = "DRAFT"
    URN_REGEX: ClassVar[re.Pattern[str]] = URN_REGEXES["DRAFT"]

    @property
    def draft_year(self) -> int:
        return int(self.parts[2])

    @property
    def jurisdiction(self) -> str:
        return self.parts[3]

    @property
    def card_locator(self) -> str:
        return self.parts[4]


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class CensusUrn(ArchivalURN):
    """Canonical Census URN ('URN:CENSUS:<YEAR>:<JURISDICTION>:<ENUMERATION_LOCATOR>')."""

    EXPECTED_NID: ClassVar[str | None] = "CENSUS"
    URN_REGEX: ClassVar[re.Pattern[str]] = URN_REGEXES["CENSUS"]

    @property
    def census_year(self) -> int:
        return int(self.parts[2])

    @property
    def jurisdiction(self) -> str:
        return self.parts[3]

    @property
    def enumeration_locator(self) -> str:
        return self.parts[4]


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class VitalCertificateUrn(ArchivalURN):
    """Canonical Vital Certificate URN ('URN:VITAL:<EVENT>:<YEAR>:<JURISDICTION>:<CERT_NUM>')."""

    EXPECTED_NID: ClassVar[str | None] = "VITAL"
    URN_REGEX: ClassVar[re.Pattern[str]] = URN_REGEXES["VITAL"]

    @property
    def event_type(self) -> str:
        return self.parts[2]

    @property
    def certificate_year(self) -> int:
        return int(self.parts[3])

    @property
    def jurisdiction(self) -> str:
        return self.parts[4]

    @property
    def certificate_number(self) -> str:
        return self.parts[5]


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class CemeteryPlotUrn(ArchivalURN):
    """Canonical Cemetery Plot URN ('URN:CEM:<FACILITY_CODE>:<PLOT_LOCATOR>')."""

    EXPECTED_NID: ClassVar[str | None] = "CEM"
    URN_REGEX: ClassVar[re.Pattern[str]] = URN_REGEXES["CEM"]

    @property
    def facility_code(self) -> str:
        return self.parts[2]

    @property
    def plot_locator(self) -> str:
        return self.parts[3]
