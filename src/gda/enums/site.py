# Name: site.py
# Path: src/gda/enums/site.py

"""Spatial jurisdiction levels, facility venues, and cemetery marker enums."""

from __future__ import annotations

from enum import StrEnum

__version__ = "0.1.0+build.r1"

__all__ = [
    "LocationType",
    "MarkerCondition",
    "MarkerMaterial",
    "MarkerType",
    "OperationalStatus",
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
    """Classification of physical venues, facilities, landmarks, and cemeteries."""

    CEMETERY = "CEMETERY"
    CHURCH = "CHURCH"
    HOSPITAL = "HOSPITAL"
    FACILITY = "FACILITY"
    RESIDENCE = "RESIDENCE"
    LANDMARK = "LANDMARK"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


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
