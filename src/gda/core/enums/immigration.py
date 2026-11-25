"""Path: src/gda/core/enums/immigration.py

Immigration voyage passage classes and naturalization proceeding stages.

Operational Role:
    Defines controlled categorical enumerations for passenger/crew passage
    classifications on arrival manifests and procedural stages in judicial
    naturalization records.
"""

from __future__ import annotations

from gda.core.enums.base import GDAStrEnum

__version__ = "1.0.0+build.2"

__all__ = [
    "ArrivalPassageClass",
    "NaturalizationStage",
]


class ArrivalPassageClass(GDAStrEnum):
    """Passenger or crew passage classification on maritime and overland arrival manifests."""

    STEERAGE = "STEERAGE"
    CABIN = "CABIN"
    SECOND_CABIN = "SECOND_CABIN"
    CREW = "CREW"
    OVERLAND = "OVERLAND"
    OTHER = "OTHER"


class NaturalizationStage(GDAStrEnum):
    """Procedural stage within a historical naturalization proceeding."""

    DECLARATION_OF_INTENTION = "DECLARATION_OF_INTENTION"
    PETITION = "PETITION"
    DEPOSITION_OF_WITNESS = "DEPOSITION_OF_WITNESS"
    OATH_OF_ALLEGIANCE = "OATH_OF_ALLEGIANCE"
    CERTIFICATE = "CERTIFICATE"
    DENIAL_OR_DISMISSAL = "DENIAL_OR_DISMISSAL"
