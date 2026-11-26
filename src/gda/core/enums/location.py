"""Path: src/gda/core/enums/location.py

Categorical enumerations for jurisdictional boundaries and administrative tiers.

Operational Role:
    Defines controlled categorical tiers for civil and geographical entities,
    enforcing a strict linear administrative hierarchy rank.
"""

from __future__ import annotations

from types import MappingProxyType

from gda.core.enums.base import GDAStrEnum

__version__ = "1.0.0+build.3"

__all__ = [
    "JurisdictionCategory",
    "LocationType",
]


class LocationType(GDAStrEnum):
    """Administrative and jurisdictional level of a geographic place."""

    CIVIL_JURISDICTION = "CIVIL_JURISDICTION"
    COUNTRY = "COUNTRY"
    STATE = "STATE"
    COUNTY = "COUNTY"
    CITY = "CITY"
    TOWNSHIP = "TOWNSHIP"
    PARISH = "PARISH"
    WARD = "WARD"
    PRECINCT = "PRECINCT"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class JurisdictionCategory(GDAStrEnum):
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
        return _ADMINISTRATIVE_RANKS[self]


_ADMINISTRATIVE_RANKS: MappingProxyType[JurisdictionCategory, int] = MappingProxyType(
    {
        JurisdictionCategory.COUNTRY: 10,
        JurisdictionCategory.STATOID: 20,
        JurisdictionCategory.COUNTY_EQUIVALENT: 30,
        JurisdictionCategory.CIVIL_TOWNSHIP: 40,
        JurisdictionCategory.MUNICIPALITY: 50,
        JurisdictionCategory.UNINCORPORATED_PLACE: 60,
        JurisdictionCategory.SPECIAL_DISTRICT: 70,
    }
)
