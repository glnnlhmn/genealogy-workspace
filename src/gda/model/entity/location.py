"""Path: src/gda/model/entity/location.py

Jurisdictional boundary and administrative entity model.

Operational Role:
    Defines the Location domain entity representing administrative jurisdictions
    (countries, states/provinces, counties, townships, municipalities, and special districts).
    Enforces relational boundary acyclicity, standardized URN formatting, administrative
    rank-ordered sorting, and composition of historical naming variants and temporal lifecycles.

Classes:
    JurisdictionCategory: Controlled administrative tier rankings.
    Location: Primary jurisdictional graph node extending BaseEntity[LocationID].
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.model.atom.geo import Coordinates
from gda.model.atom.id import LocationID
from gda.model.base.entity import BaseEntity
from gda.model.base.name import HistoricalName, NameStatus
from gda.model.base.time_period import TimePeriod

__version__ = "1.0.0+build.22"

__all__ = [
    "HistoricalName",
    "JurisdictionCategory",
    "Location",
    "NameStatus",
]

_LOCATION_ID_PATTERN: re.Pattern[str] = re.compile(r"^LOC-\d{6}$")
_LOCATION_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:loc:[a-z0-9_:\-]+$")


class JurisdictionCategory(StrEnum):
    """Hierarchical administrative categorization for civil jurisdictions."""

    COUNTRY = "COUNTRY"
    STATOID = "STATOID"
    COUNTY_EQUIVALENT = "COUNTY_EQUIVALENT"
    CIVIL_TOWNSHIP = "CIVIL_TOWNSHIP"
    MUNICIPALITY = "MUNICIPALITY"
    UNINCORPORATED_PLACE = "UNINCORPORATED_PLACE"
    SPECIAL_DISTRICT = "SPECIAL_DISTRICT"

    @property
    def administrative_rank(self) -> int:
        """Return numerical hierarchy ranking (lower number = higher administrative tier)."""
        ranks = {
            self.COUNTRY: 10,
            self.STATOID: 20,
            self.COUNTY_EQUIVALENT: 30,
            self.CIVIL_TOWNSHIP: 40,
            self.MUNICIPALITY: 40,
            self.UNINCORPORATED_PLACE: 50,
            self.SPECIAL_DISTRICT: 60,
        }
        return ranks[self]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class Location(BaseEntity[LocationID]):
    """Administrative jurisdiction entity representing a civil territory or government body."""

    name: str = Field(
        ..., description="Canonical standard primary name of the jurisdiction."
    )
    category: JurisdictionCategory = Field(
        ..., description="Standardized administrative classification tier."
    )
    canonical_urn: str = Field(
        ...,
        description="Deterministic unique URN (e.g., 'urn:gda:loc:us:nh:merrimack:bow').",
    )
    parent_id: LocationID | None = Field(
        default=None, description="Direct parent governing jurisdiction."
    )
    historical_names: list[HistoricalName] = Field(
        default_factory=list, description="Date-bounded historical naming variants."
    )
    alternate_names: list[str] = Field(
        default_factory=list,
        description="Colloquial, vernacular, or common naming aliases.",
    )
    associated_jurisdiction_ids: list[LocationID] = Field(
        default_factory=list,
        description="Overlapping or affiliated jurisdictional entities.",
    )
    predecessor_ids: list[LocationID] = Field(
        default_factory=list,
        description="Prior jurisdictions partitioned or merged into this.",
    )
    successor_ids: list[LocationID] = Field(
        default_factory=list,
        description="Subsequent jurisdictions created from this entity.",
    )
    is_primary_local_authority: bool = Field(
        default=False,
        description="True if this civil level holds primary record-keeping precedence.",
    )
    is_unincorporated: bool = Field(
        default=False,
        description="True if territory lacks formal municipal incorporation.",
    )
    period: TimePeriod | None = Field(
        default=None,
        description="Temporal bounds spanning establishment to dissolution.",
    )
    coordinates: Coordinates | None = Field(
        default=None, description="Centroid or benchmark spatial coordinates."
    )

    def __post_init__(self) -> None:
        """Enforce domain invariants, relational integrity, and parent boundary checks."""
        super().__post_init__()

        if not isinstance(self.id, LocationID):
            raise TypeError(
                f"Location 'id' must be an instance of LocationID, got {type(self.id).__name__}."
            )

        raw_id = self.id.value
        if not _LOCATION_ID_PATTERN.match(raw_id):
            raise ModelFormatError(
                f"Invalid LocationID format: '{raw_id}'. Must match 'LOC-######'."
            )

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Location cannot be superseded by itself.")

        if not self.name or not self.name.strip():
            raise ModelFormatError("Location 'name' cannot be empty or whitespace.")

        if not _LOCATION_URN_PATTERN.match(self.canonical_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:loc:<namespace>'"
            )

        if self.parent_id is not None and self.parent_id == self.id:
            raise ModelFormatError("Location cannot be its own parent.")

        if self.id in self.associated_jurisdiction_ids:
            raise ModelFormatError(
                "Location cannot reference itself in associated_jurisdiction_ids."
            )

        if self.id in self.predecessor_ids:
            raise ModelFormatError(
                "Location cannot reference itself in predecessor_ids."
            )

        if self.id in self.successor_ids:
            raise ModelFormatError("Location cannot reference itself in successor_ids.")

        if len(self.associated_jurisdiction_ids) != len(
            set(self.associated_jurisdiction_ids)
        ):
            raise ModelFormatError(
                "Duplicate entries found in associated_jurisdiction_ids."
            )

        if len(self.predecessor_ids) != len(set(self.predecessor_ids)):
            raise ModelFormatError("Duplicate entries found in predecessor_ids.")

        if len(self.successor_ids) != len(set(self.successor_ids)):
            raise ModelFormatError("Duplicate entries found in successor_ids.")

    @property
    def category_rank(self) -> int:
        """Expose administrative tier sorting priority."""
        return self.category.administrative_rank

    @property
    def sort_key(self) -> tuple[int, str]:
        """Deterministic ordering key sorting by hierarchy tier then primary name."""
        return (self.category_rank, self.name.lower())

    def __str__(self) -> str:
        """Render concise human-readable jurisdictional representation."""
        return f"{self.name} [{self.category.value}] ({self.id.value})"
