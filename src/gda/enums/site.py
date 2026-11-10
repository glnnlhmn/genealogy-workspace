"""Path: src/gda/enums/site.py

Spatial jurisdiction levels, facility venues, and cemetery marker enums.

Operational Role:
    Defines controlled categorical enumerations for physical site/venue
    classifications, facility operational lifecycles, and cemetery monument
    typologies, materials, and conditions.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.0.0+build.5"

__all__ = [
    "MarkerCondition",
    "MarkerMaterial",
    "MarkerType",
    "OperationalStatus",
    "SiteType",
]


class SiteType(StrEnum):
    """Classification of physical venues, structures, landmarks, and cemeteries."""

    BUSINESS = "BUSINESS"
    CEMETERY = "CEMETERY"
    CHURCH = "CHURCH"
    COMMERCIAL = "COMMERCIAL"
    FACILITY = "FACILITY"
    GOVERNMENT = "GOVERNMENT"
    HOSPITAL = "HOSPITAL"
    LANDMARK = "LANDMARK"
    MILITARY = "MILITARY"
    REPOSITORY = "REPOSITORY"
    RESIDENCE = "RESIDENCE"
    SCHOOL = "SCHOOL"
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
