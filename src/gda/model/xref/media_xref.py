"""Path: src/gda/model/xref/media_xref.py

Associative cross-reference linking domain entities to media assets.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.model.atom.id import FactID, FamilyID, IndividualID, MediaID, SiteID
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.1"

__all__ = ["MediaRegion", "MediaXRef"]

# Normalized pixel coordinates: [ymin, xmin, ymax, xmax] bounded between 0.0 and 1.0
BoundingBox = tuple[float, float, float, float]
LinkedEntityID = IndividualID | FamilyID | FactID | SiteID


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class MediaRegion:
    """Normalized bounding region identifying a target subject within an image."""

    ymin: float = Field(..., ge=0.0, le=1.0)
    xmin: float = Field(..., ge=0.0, le=1.0)
    ymax: float = Field(..., ge=0.0, le=1.0)
    xmax: float = Field(..., ge=0.0, le=1.0)

    def __post_init__(self) -> None:
        if self.ymin >= self.ymax:
            raise ValueError(f"ymin ({self.ymin}) must be less than ymax ({self.ymax})")
        if self.xmin >= self.xmax:
            raise ValueError(f"xmin ({self.xmin}) must be less than xmax ({self.xmax})")


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class MediaXRef:
    """Associative graph edge binding an entity to a media artifact."""

    entity_id: LinkedEntityID = Field(
        ..., description="Target domain entity identifier."
    )
    media_id: MediaID = Field(..., description="Target media asset identifier.")
    is_primary: bool = Field(
        default=False,
        description="Whether this media item serves as the primary visual avatar for the entity.",
    )
    caption: str | None = Field(
        default=None,
        description="Contextual caption specific to this entity's presence in the media.",
    )
    region: MediaRegion | None = Field(
        default=None,
        description="Optional spatial coordinates isolating the entity within the image.",
    )
    audit: AuditStamp = Field(
        default_factory=AuditStamp.now_utc,
        description="Lifecycle timestamps tracking edge creation and modifications.",
    )
