"""Path: src/gda/model/entity/fact.py

Genealogical fact and life event entity model representing historical assertions.
"""

from __future__ import annotations

import re
from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.core import AssociatedRole, FactType
from gda.model.atom.date import EventDate
from gda.model.atom.id import FactID, FamilyID, IndividualID, LocationID, SiteID
from gda.model.base.entity import BaseEntity
from gda.model.base.source_reference import SourceReference
from gda.model.base.time_period import TimePeriod

__version__ = "1.0.0+build.2"

__all__ = ["Fact", "FactParticipant"]

_FACT_ID_PATTERN: re.Pattern[str] = re.compile(r"^FID-\d{6,}$")
_FACT_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:fact:[a-z0-9_:\-]+$")


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class FactParticipant:
    """Associative linkage connecting an individual to a fact in a secondary role."""

    individual_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the participating individual.",
    )
    role: AssociatedRole = Field(
        default=AssociatedRole.WITNESS,
        description="Role in event: WITNESS, CLERGY, INFORMANT, COMPANION, etc.",
    )
    notes: str | None = Field(
        default=None,
        description="Optional specific notes on participation or testimony.",
    )

    def __str__(self) -> str:
        """Render concise string representation of the participant."""
        suffix = f" ({self.notes})" if self.notes else ""
        return f"{self.individual_id.value} [{self.role.value}]{suffix}"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class Fact(BaseEntity[FactID]):
    """Evidentiary event assertion anchoring entities to time, place, and citations."""

    canonical_urn: str = Field(
        ...,
        description="Deterministic lookup URN (e.g., 'urn:gda:fact:smith_birth_1842').",
    )
    fact_type: FactType = Field(
        ...,
        description="Standard event classification (BIRTH, DEATH, CENSUS, RESIDENCE, etc.).",
    )
    title: str = Field(
        ...,
        description="Concise summary or headline for timeline displays.",
    )
    primary_subject_id: IndividualID | FamilyID = Field(
        ...,
        description="Primary entity (IndividualID or FamilyID) about whom the fact is asserted.",
    )
    date: EventDate | TimePeriod | None = Field(
        default=None,
        description="Point-in-time EventDate or bounded TimePeriod duration.",
    )
    location_id: LocationID | None = Field(
        default=None,
        description="Macro-jurisdictional geographic anchor (Town, County, State, Country).",
    )
    site_id: SiteID | None = Field(
        default=None,
        description="Micro-physical place anchor (Cemetery, Church, Homestead, Hospital).",
    )
    value: str | None = Field(
        default=None,
        description="Specific assertion attribute (e.g., 'Blacksmith', 'Pneumonia').",
    )
    description: str | None = Field(
        default=None,
        description="Structured transcription extract or itemized factual details.",
    )
    narrative: str | None = Field(
        default=None,
        description="Free-form biographical or life-story prose narrative.",
    )
    participants: list[FactParticipant] = Field(
        default_factory=list,
        description="Secondary individuals involved in the assertion with contextual roles.",
    )
    citations: list[SourceReference] = Field(
        default_factory=list,
        description="Documentary evidentiary citations linking the fact to supporting sources.",
    )

    _ID_PATTERN: ClassVar[re.Pattern[str]] = _FACT_ID_PATTERN
    _URN_PATTERN: ClassVar[re.Pattern[str]] = _FACT_URN_PATTERN

    def __post_init__(self) -> None:
        """Enforce domain invariants, participant uniqueness, and relational integrity."""
        super().__post_init__()

        if not isinstance(self.id, FactID):
            raise TypeError(
                f"Fact 'id' must be an instance of FactID, got {type(self.id).__name__}."
            )

        raw_id = self.id.value
        if not self._ID_PATTERN.match(raw_id):
            raise ModelFormatError(
                f"Invalid FactID format: '{raw_id}'. Must match 'FID-######'."
            )

        if not self._URN_PATTERN.match(self.canonical_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:fact:<slug>'."
            )

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Fact cannot be superseded by itself.")

        participant_ids = [p.individual_id for p in self.participants]
        if len(participant_ids) != len(set(participant_ids)):
            raise ModelFormatError(
                "Duplicate individual entries found in participants."
            )

        if (
            isinstance(self.primary_subject_id, IndividualID)
            and self.primary_subject_id in participant_ids
        ):
            raise ModelFormatError(
                "Primary subject cannot also be listed as a secondary participant."
            )

    @property
    def participant_ids(self) -> list[IndividualID]:
        """Convenience accessor returning ordered list of participant IndividualIDs."""
        return [p.individual_id for p in self.participants]

    @property
    def citation_count(self) -> int:
        """Total number of evidentiary source citations attached to this fact."""
        return len(self.citations)

    @property
    def participant_count(self) -> int:
        """Total number of secondary participants recorded."""
        return len(self.participants)

    def __str__(self) -> str:
        """Render concise human-readable fact summary."""
        date_str = f" on {self.date}" if self.date else ""
        return (
            f"Fact [{self.fact_type.value}] '{self.title}' for "
            f"{self.primary_subject_id.value}{date_str} ({self.id.value})"
        )
