"""Path: src/gda/core/enums/site.py

Spatial jurisdiction levels, facility venues, and cemetery marker enums.

Operational Role:
    Defines controlled categorical enumerations for physical site/venue
    classifications, facility operational lifecycles, and cemetery monument
    typologies, materials, and conditions.
"""

from __future__ import annotations

from gda.core.enums.base import GDAStrEnum

__version__ = "1.0.0+build.2"

__all__ = [
    "MarkerCondition",
    "MarkerMaterial",
    "MarkerType",
    "OperationalStatus",
    "SiteType",
]


class SiteType(GDAStrEnum):
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


class OperationalStatus(GDAStrEnum):
    """Operational lifecycle status of physical sites and facilities."""

    ACTIVE = "ACTIVE"
    DEFUNCT = "DEFUNCT"
    ABANDONED = "ABANDONED"
    HISTORICAL = "HISTORICAL"
    UNKNOWN = "UNKNOWN"


class MarkerType(GDAStrEnum):
    """Typology of cemetery headstones, monuments, and memorial markers."""

    UPRIGHT_HEADSTONE = "UPRIGHT_HEADSTONE"
    FLAT_MARKER = "FLAT_MARKER"
    SLANT = "SLANT"
    OBELISK = "OBELISK"
    LEDGER = "LEDGER"
    TABLE_TOMB = "TABLE_TOMB"
    FOOTSTONE = "FOOTSTONE"
    MONUMENT = "MONUMENT"
    OTHER = "OTHER"


class MarkerMaterial(GDAStrEnum):
    """Material composition of cemetery headstones and markers."""

    MARBLE = "MARBLE"
    GRANITE = "GRANITE"
    SANDSTONE = "SANDSTONE"
    LIMESTONE = "LIMESTONE"
    SLATE = "SLATE"
    FIELDSTONE = "FIELDSTONE"
    BRONZE = "BRONZE"
    OTHER = "OTHER"


class MarkerCondition(GDAStrEnum):
    """Preservation and physical condition of cemetery markers."""

    SOUND = "SOUND"
    WEATHERED = "WEATHERED"
    BROKEN = "BROKEN"
    BROKEN_REPAIRED = "BROKEN_REPAIRED"
    SUNKEN = "SUNKEN"
    ILLEGIBLE = "ILLEGIBLE"
    OVERGROWN = "OVERGROWN"
