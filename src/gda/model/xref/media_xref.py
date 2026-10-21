"""Path: src/gda/model/xref/media_xref.py

Associative relational cross-reference edge linking domain entities to media assets.

Operational Role:
    Defines the immutable relational edge ('MediaXRef') connecting domain entities
    (Individual, Family, Fact, Site, Location) to digital media assets. Enforces
    UUID boundaries, Pydantic immutability, and boundary validation.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.model.atom.date import EventDate, IsoTimestamp
from gda.model.atom.id import AtomID

__version__ = "1.0.0+build.4"

__all__ = ["MediaXRef"]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class MediaXRef:
    """Relational cross-reference edge linking a domain entity to a digital media asset."""

    entity_id: AtomID = Field(
        ...,
        description="Linked domain entity identifier (e.g., IND-, FAM-, FID-, SIT-, LOC-).",
    )
    media_id: UUID = Field(
        ...,
        description="Target digital media asset identifier (UUID).",
    )
    xref_id: UUID = Field(
        default_factory=uuid4,
        description="Unique primary identifier for the cross-reference record.",
    )
    caption: str | None = Field(
        default=None,
        description="Contextual description, narrative label, or transcription note.",
    )
    date: EventDate | None = Field(
        default=None,
        description="Genealogical event date representation for media capture or association.",
    )
    compiled_at: IsoTimestamp = Field(
        default_factory=IsoTimestamp.now_utc,
        description="Edge generation and indexing timestamp.",
    )
