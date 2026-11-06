"""Path: src/gda/model/atom/urn.py

Archival Uniform Resource Name (URN) primitives using Pydantic dataclasses.

Operational Role:
    Provides structured, immutable, and regex-validated URN tokens for canonical
    evidentiary records, citations, census schedules, military drafts, vital
    certificates, and cemetery locations across the archive.

Architecture:
    - ArchivalURN: Abstract base primitive for hierarchical delimited URN tokens.
    - SourceURN: Generic archival source citation identifier (URN:SRC:...).
    - MilitaryDraftUrn: Military conscription record identifier (URN:DRAFT:...).
    - CensusUrn: Population census schedule identifier (URN:CENSUS:...).
    - VitalCertificateUrn: Civil and parish vital registration (URN:VITAL:...).
    - CemeteryPlotUrn: Burial ground and cemetery plot locator (URN:CEM:...).
"""

from __future__ import annotations

import re
from typing import ClassVar

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger

__version__ = "1.0.0+build.1"

_logger = GDALogger(__name__)


# ==============================================================================
# BASE ARCHIVAL URN PRIMITIVE
# ==============================================================================


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class ArchivalURN(IntrospectableMixin):
    """Abstract base primitive for multi-part archival URN identifiers.

    Attributes:
        value: Canonical uniform resource name string.
    """

    value: str
    EXPECTED_SCHEME: ClassVar[str] = "URN"
    EXPECTED_NID: ClassVar[str | None] = None
    URN_REGEX: ClassVar[re.Pattern[str]] = re.compile(
        r"^URN:[A-Z0-9_-]+(:[A-Za-z0-9_.-]+)+$",
    )

    def __post_init__(self) -> None:
        """Validate URN token syntax and namespace conformity."""
        val = self.value.strip()

        if not val or not self.URN_REGEX.match(val):
            err_msg = f"Invalid {self.__class__.__name__} syntax: '{self.value}'"
            _logger.debug("URN validation failed", details={"value": self.value})
            raise ModelFormatError(err_msg, details={"value": self.value})

        parts = val.split(":")
        scheme = parts[0]
        nid = parts[1] if len(parts) > 1 else ""

        if scheme != self.EXPECTED_SCHEME:
            err_msg = (
                f"Invalid URN scheme '{scheme}' for {self.__class__.__name__}; "
                f"expected '{self.EXPECTED_SCHEME}'."
            )
            _logger.debug("URN scheme mismatch", details={"scheme": scheme})
            raise ModelFormatError(err_msg, details={"scheme": scheme})

        if self.EXPECTED_NID is not None and nid != self.EXPECTED_NID:
            err_msg = (
                f"Invalid URN namespace '{nid}' for {self.__class__.__name__}; "
                f"expected '{self.EXPECTED_NID}'."
            )
            _logger.debug("URN NID mismatch", details={"nid": nid})
            raise ModelFormatError(err_msg, details={"nid": nid})

        object.__setattr__(self, "value", val)

    @property
    def parts(self) -> list[str]:
        """Return delimited URN segments."""
        return self.value.split(":")

    @property
    def nid(self) -> str:
        """Return namespace identifier segment (e.g., 'SRC', 'DRAFT', 'CENSUS')."""
        return self.parts[1]

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.value}')"


# ==============================================================================
# SPECIALIZED DOMAIN URN PRIMITIVES
# ==============================================================================


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class SourceURN(ArchivalURN):
    """Canonical archival URN identifying a primary evidentiary source record.

    Format: URN:SRC:<YEAR>:<JURISDICTION>:<RECORD_LOCATOR>
    Example: URN:SRC:1917:NH_MERRIMACK:DOC_000101
    """

    EXPECTED_NID: ClassVar[str | None] = "SRC"
    URN_REGEX: ClassVar[re.Pattern[str]] = re.compile(
        r"^URN:SRC:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    )

    @property
    def year(self) -> int:
        """Return record origin year component."""
        return int(self.parts[2])

    @property
    def jurisdiction(self) -> str:
        """Return record civil jurisdiction component."""
        return self.parts[3]

    @property
    def locator(self) -> str:
        """Return specific documentary locator component."""
        return self.parts[4]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class MilitaryDraftUrn(ArchivalURN):
    """Canonical archival URN identifying a military conscription registration card.

    Format: URN:DRAFT:<YEAR>:<JURISDICTION>:<BOARD_OR_CARD_LOCATOR>
    Example: URN:DRAFT:1917:NH_MERRIMACK:CARD_001
    """

    EXPECTED_NID: ClassVar[str | None] = "DRAFT"
    URN_REGEX: ClassVar[re.Pattern[str]] = re.compile(
        r"^URN:DRAFT:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    )

    @property
    def draft_year(self) -> int:
        """Return military conscription year."""
        return int(self.parts[2])

    @property
    def jurisdiction(self) -> str:
        """Return state and county/board jurisdiction."""
        return self.parts[3]

    @property
    def card_locator(self) -> str:
        """Return specific registration card locator."""
        return self.parts[4]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class CensusUrn(ArchivalURN):
    """Canonical archival URN identifying a federal or state census enumeration.

    Format: URN:CENSUS:<YEAR>:<JURISDICTION>:<ED_SHEET_LINE>
    Example: URN:CENSUS:1920:NH_MERRIMACK:ED12_S04B_L02
    """

    EXPECTED_NID: ClassVar[str | None] = "CENSUS"
    URN_REGEX: ClassVar[re.Pattern[str]] = re.compile(
        r"^URN:CENSUS:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    )

    @property
    def census_year(self) -> int:
        """Return enumeration census year."""
        return int(self.parts[2])

    @property
    def jurisdiction(self) -> str:
        """Return civil district jurisdiction."""
        return self.parts[3]

    @property
    def enumeration_locator(self) -> str:
        """Return enumeration district, sheet, and line locator."""
        return self.parts[4]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class VitalCertificateUrn(ArchivalURN):
    """Canonical archival URN identifying a civil or parish vital certificate.

    Format: URN:VITAL:<EVENT_TYPE>:<YEAR>:<JURISDICTION>:<CERT_NUMBER>
    Example: URN:VITAL:BIRTH:1905:NH_CONCORD:CERT_00451
    """

    EXPECTED_NID: ClassVar[str | None] = "VITAL"
    URN_REGEX: ClassVar[re.Pattern[str]] = re.compile(
        r"^URN:VITAL:(BIRTH|MARRIAGE|DEATH):[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    )

    @property
    def event_type(self) -> str:
        """Return vital event type (BIRTH, MARRIAGE, DEATH)."""
        return self.parts[2]

    @property
    def certificate_year(self) -> int:
        """Return certificate registration year."""
        return int(self.parts[3])

    @property
    def jurisdiction(self) -> str:
        """Return issuing municipality or county jurisdiction."""
        return self.parts[4]

    @property
    def certificate_number(self) -> str:
        """Return unique filing or certificate registration number."""
        return self.parts[5]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class CemeteryPlotUrn(ArchivalURN):
    """Canonical archival URN identifying an exact cemetery burial plot or monument.

    Format: URN:CEM:<FACILITY_CODE>:<SECTION_LOT_GRAVE>
    Example: URN:CEM:NH_BLOSSOM_HILL:SEC_A_LOT_12_G1
    """

    EXPECTED_NID: ClassVar[str | None] = "CEM"
    URN_REGEX: ClassVar[re.Pattern[str]] = re.compile(
        r"^URN:CEM:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    )

    @property
    def facility_code(self) -> str:
        """Return unique cemetery or churchyard identifier code."""
        return self.parts[2]

    @property
    def plot_locator(self) -> str:
        """Return specific section, lot, and grave position locator."""
        return self.parts[3]


__all__ = [
    "ArchivalURN",
    "CemeteryPlotUrn",
    "CensusUrn",
    "MilitaryDraftUrn",
    "SourceURN",
    "VitalCertificateUrn",
]
