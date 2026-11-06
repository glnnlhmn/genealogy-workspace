"""Path: src/gda/enums/site.py

Spatial jurisdiction levels, facility venues, and cemetery marker enums.

Operational Role:
    Defines controlled categorical enumerations for spatial jurisdictions,
    physical site/venue classifications, facility operational lifecycles,
    and cemetery monument typologies, materials, and conditions.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.1.0+build.1"

__all__ = [
    "LocationType",
    "MarkerCondition",
    "MarkerMaterial",
    "MarkerType",
    "OperationalStatus",
    "SiteCategory",
    "SiteType",
]


class LocationType(StrEnum):
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


class SiteType(StrEnum):
    """Classification of physical venues, structures, landmarks, and cemeteries."""

    CEMETERY = "CEMETERY"
    CHURCH = "CHURCH"
    COMMERCIAL = "COMMERCIAL"
    GOVERNMENT = "GOVERNMENT"
    HOSPITAL = "HOSPITAL"
    LANDMARK = "LANDMARK"
    MILITARY = "MILITARY"
    REPOSITORY = "REPOSITORY"
    RESIDENCE = "RESIDENCE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


# Backward compatibility alias for legacy SiteCategory imports
SiteCategory = SiteType


class OperationalStatus(StrEnum):
    """Operational lifecycle status of physical sites and facilities."""

    ACTIVE = "ACTIVE"
    DEFUNCT = "DEFUNCT"
    ABANDONED = "ABANDONED"
    HISTORICAL = "HISTORICAL"
    UNKNOWN = "UNKNOWN"


class MarkerType(StrEnum):
    """Typology of cemetery headstones, monuments, and memorial markers."""

    UPRIGHT_HEADSTONE = "Upright Headstone"
    FLAT_MARKER = "Flat Marker"
    SLANT = "Slant"
    OBELISK = "Obelisk"
    LEDGER = "Ledger"
    TABLE_TOMB = "Table Tomb"
    FOOTSTONE = "Footstone"
    MONUMENT = "Monument"
    OTHER = "Other"


class MarkerMaterial(StrEnum):
    """Material composition of cemetery headstones and markers."""

    MARBLE = "Marble"
    GRANITE = "Granite"
    SANDSTONE = "Sandstone"
    LIMESTONE = "Limestone"
    SLATE = "Slate"
    FIELDSTONE = "Fieldstone"
    BRONZE = "Bronze"
    OTHER = "Other"


class MarkerCondition(StrEnum):
    """Preservation and physical condition of cemetery markers."""

    SOUND = "Sound"
    WEATHERED = "Weathered"
    BROKEN = "Broken"
    BROKEN_REPAIRED = "Broken/Repaired"
    SUNKEN = "Sunken"
    ILLEGIBLE = "Illegible"
    OVERGROWN = "Overgrown"
