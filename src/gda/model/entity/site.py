"""Path: src/gda/model/entity/site.py

Physical venue and archival site entity model implementations.

Operational Role:
    Defines Site representing physical venues, structures, cemeteries, churches,
    and repositories situated within civil jurisdictions. Implements structured
    temporal naming evolution, controlled site categorization, spatial/address
    anchoring, and domain boundary validations.

Classes:
    SiteCategory: Controlled classification of physical venue types.
    Site: Primary site node inheriting from BaseEntity[SiteID].
    SiteEntityModel: Backward compatibility alias.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.model.atom.date import EventDate
from gda.model.atom.geo import Coordinates
from gda.model.atom.id import LocationID, SiteID
from gda.model.base.address import Address
from gda.model.base.entity import BaseEntity
from gda.model.base.name import HistoricalName
from gda.model.base.time_period import TimePeriod

__version__ = "1.0.0+build.6"

__all__ = [
    "Site",
    "SiteCategory",
    "SiteEntityModel",
]

_SITE_ID_PATTERN: re.Pattern[str] = re.compile(r"^SID-\d{6}$")
_SITE_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:site:[a-z0-9_:-]+$")


class SiteCategory(StrEnum):
    """Controlled classification of physical venues, facilities, and landmarks."""

    CEMETERY = "CEMETERY"
    CHURCH = "CHURCH"
    RESIDENCE = "RESIDENCE"
    HOSPITAL = "HOSPITAL"
    GOVERNMENT = "GOVERNMENT"
    MILITARY = "MILITARY"
    REPOSITORY = "REPOSITORY"
    COMMERCIAL = "COMMERCIAL"
    LANDMARK = "LANDMARK"
    OTHER = "OTHER"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class Site(BaseEntity[SiteID]):
    """Primary physical venue, facility, or landmark entity model."""

    name: str = Field(..., description="Standardized primary name of the site.")
    category: SiteCategory = Field(
        ..., description="Controlled functional classification of the physical venue."
    )
    canonical_urn: str = Field(
        ...,
        description="Semantic deterministic lookup URN (e.g., 'urn:gda:site:us:nh:bow:cemetery').",
    )
    location_id: LocationID = Field(
        ..., description="Foreign key reference to governing civil jurisdiction."
    )
    address: Address | None = Field(
        default=None, description="Optional physical or street-level address."
    )
    coordinates: Coordinates | None = Field(
        default=None,
        description="Geographic coordinates marking site entrance or centroid.",
    )
    historical_names: list[HistoricalName] = Field(
        default_factory=list, description="Date-bounded historical naming assertions."
    )
    alternate_names: list[str] = Field(
        default_factory=list, description="Colloquial or vernacular naming variants."
    )
    period: TimePeriod | None = Field(
        default=None,
        description="Structured temporal bounds spanning establishment to closure.",
    )
    is_active: bool = Field(
        default=True,
        description="Indicates whether the facility is currently extant or operational.",
    )

    def __post_init__(self) -> None:
        """Enforce domain invariants and structural boundary guards."""
        super().__post_init__()

        if not isinstance(self.id, SiteID):
            raise TypeError(
                f"Site 'id' must be an instance of SiteID, got {type(self.id).__name__}."
            )

        raw_id = self.id.value
        if not _SITE_ID_PATTERN.match(raw_id):
            raise ModelFormatError(
                f"Invalid SiteID format: '{raw_id}'. Must match 'SID-######'."
            )

        if not self.name or not self.name.strip():
            raise ModelFormatError("Site 'name' cannot be empty or whitespace.")

        if not _SITE_URN_PATTERN.match(self.canonical_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:site:<namespace>'"
            )

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Site cannot be superseded by itself.")

    @property
    def date_established(self) -> EventDate | None:
        """Convenience accessor for site establishment date from period."""
        return self.period.start_date if self.period is not None else None

    @property
    def date_closed(self) -> EventDate | None:
        """Convenience accessor for site closure date from period."""
        return self.period.end_date if self.period is not None else None

    def __str__(self) -> str:
        """Return concise human-readable string representation of the site entity."""
        return f"{self.name} [{self.category.value}] ({self.id.value})"


SiteEntityModel = Site
