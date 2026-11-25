"""Path: src/gda/core/enums/fiscal.py

Fiscal, taxation, housing tenure, and citizenship status enumerations.

Operational Role:
    Defines canonical enumerations for taxpayer classifications, home ownership
    and mortgage tenure, citizenship/naturalization status, and residential
    directory occupancy classifications.
"""

from __future__ import annotations

from gda.core.enums.base import GDAStrEnum

__version__ = "1.0.0+build.2"

__all__ = [
    "CitizenshipStatus",
    "HomeOwnership",
    "ResidentialStatus",
    "TaxpayerClassification",
]


class TaxpayerClassification(GDAStrEnum):
    """Historical tax roll assessment classifications."""

    FREEHOLDER = "FREEHOLDER"
    TENANT = "TENANT"
    SINGLE_FREEMAN = "SINGLE_FREEMAN"
    INMATE = "INMATE"
    WIDOW = "WIDOW"


class HomeOwnership(GDAStrEnum):
    """Census and property housing tenure classifications."""

    OWNED = "OWNED"
    RENTED = "RENTED"
    FREE = "FREE"
    MORTGAGED = "MORTGAGED"
    UNKNOWN = "UNKNOWN"


class CitizenshipStatus(GDAStrEnum):
    """Recorded national citizenship and naturalization status."""

    NATIVE_BORN = "NATIVE_BORN"
    NATURALIZED = "NATURALIZED"
    ALIEN = "ALIEN"
    DECLARANT = "DECLARANT"
    NON_DECLARANT = "NON_DECLARANT"
    UNKNOWN = "UNKNOWN"


class ResidentialStatus(GDAStrEnum):
    """City directory and household occupancy status classifications."""

    HOUSEHOLDER = "HOUSEHOLDER"
    BOARDER = "BOARDER"
    ROOMS = "ROOMS"
    TENANT = "TENANT"
    WIDOW = "WIDOW"
