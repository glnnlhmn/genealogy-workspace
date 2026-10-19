"""Path: src/gda/model/base/name.py

Canonical personal, jurisdictional, and historical naming representations.

Operational Role:
    Defines foundational naming models across the digital archive. Provides
    CanonicalName for individual genealogical personas, and HistoricalName
    with NameStatus for evolutionary naming across civil jurisdictions,
    physical sites, and custodial repositories.

Classes:
    NameStatus: Historical and genealogical naming status classifications.
    HistoricalName: Temporal naming assertion for jurisdictions, sites, and venues.
    CanonicalName: Structured personal name preserving raw string and components.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.enums.vital import NameStatus
from gda.model.base.time_period import TimePeriod

__version__ = "1.0.0+build.2"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class HistoricalName(IntrospectableMixin):
    """Temporal and evolutionary naming record for jurisdictions, sites, and venues."""

    raw_name: str = Field(
        ..., description="Verbatim historical name as recorded in sources."
    )
    canonical_name: str | None = Field(
        default=None, description="Standardized, modern or normalized variant."
    )
    status: NameStatus = Field(
        default=NameStatus.HISTORICAL, description="Archival naming classification."
    )
    valid_period: TimePeriod | None = Field(
        default=None, description="Optional temporal bounds when this name was active."
    )
    alternate_spellings: list[str] = Field(
        default_factory=list,
        description="Phonetic, vernacular, or transcription spellings.",
    )
    notes: str | None = Field(
        default=None, description="Archival justification or etymological notes."
    )

    def __post_init__(self) -> None:
        """Enforce domain naming invariants."""
        if not self.raw_name or not self.raw_name.strip():
            raise ModelFormatError(
                "HistoricalName 'raw_name' cannot be empty or whitespace."
            )

        if self.canonical_name is not None and not self.canonical_name.strip():
            raise ModelFormatError(
                "HistoricalName 'canonical_name' cannot be empty or whitespace if provided."
            )

        if len(self.alternate_spellings) != len(set(self.alternate_spellings)):
            raise ModelFormatError("Duplicate entries found in alternate_spellings.")

    @property
    def display_name(self) -> str:
        """Return standardized canonical name if available, falling back to raw name."""
        return self.canonical_name if self.canonical_name else self.raw_name

    def __str__(self) -> str:
        """Render concise human-readable historical name description."""
        if self.valid_period:
            return f"{self.display_name} ({self.status.value}: {self.valid_period})"
        return f"{self.display_name} ({self.status.value})"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class CanonicalName(IntrospectableMixin):
    """Structured personal name preserving verbatim string and parsed components."""

    raw_name: str = Field(
        ..., description="Verbatim personal name as recorded in source."
    )
    given: str | None = Field(default=None, description="Given or first name.")
    middle: str | None = Field(default=None, description="Middle name or initial.")
    surname: str | None = Field(
        default=None, description="Patronymic or family surname."
    )
    suffix: str | None = Field(
        default=None, description="Generational or honorific suffix."
    )
    maiden_name: str | None = Field(
        default=None, description="Birth or un-married surname."
    )

    def __post_init__(self) -> None:
        """Validate naming invariants."""
        if not self.raw_name or not self.raw_name.strip():
            raise ModelFormatError(
                "CanonicalName 'raw_name' cannot be empty or whitespace."
            )

    @property
    def full_name(self) -> str:
        """Construct structured personal name string from present components."""
        parts: list[str] = []
        if self.given:
            parts.append(self.given)
        if self.middle:
            parts.append(self.middle)
        if self.surname:
            parts.append(self.surname)
        if self.suffix:
            parts.append(self.suffix)
        return " ".join(parts) if parts else self.raw_name

    def __str__(self) -> str:
        """Return full structured personal name representation."""
        return self.full_name
