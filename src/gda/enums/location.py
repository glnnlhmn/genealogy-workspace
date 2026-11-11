"""Path: src/gda/enums/location.py

Backward-compatible re-export facade routing location and jurisdiction enums to gda.core.enums.
"""

from __future__ import annotations

from gda.core.enums import (
    CitizenshipStatus,
    HomeOwnership,
    JurisdictionCategory,
    LocationType,
    ResidentialStatus,
    TaxpayerClassification,
)

__all__ = [
    "CitizenshipStatus",
    "HomeOwnership",
    "JurisdictionCategory",
    "LocationType",
    "ResidentialStatus",
    "TaxpayerClassification",
]
