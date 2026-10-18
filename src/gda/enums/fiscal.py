# Name: fiscal.py
# Path: src/gda/enums/fiscal.py

"""Economic, real property tenure, directory status, and tax classification enums."""

from __future__ import annotations

from enum import StrEnum

__version__ = "0.1.0+build.r1"

__all__ = [
    "CitizenshipStatus",
    "HomeOwnership",
    "ResidentialStatus",
    "TaxpayerClassification",
]


class TaxpayerClassification(StrEnum):
    """Historical tax roll classifications for individuals."""

    FREEHOLDER = "Freeholder"
    TENANT = "Tenant"
    SINGLE_FREEMAN = "Single Freeman"
    INMATE = "Inmate"
    WIDOW = "Widow"


class HomeOwnership(StrEnum):
    """Tenure status of home recorded on federal census schedules."""

    OWNED = "Owned"
    RENTED = "Rented"
    FREE = "Free"
    MORTGAGED = "Mortgaged"
    UNKNOWN = "Unknown"


class CitizenshipStatus(StrEnum):
    """Naturalization and legal residency classification on census returns."""

    NATIVE_BORN = "Native Born"
    NATURALIZED = "Naturalized"
    ALIEN = "Alien"
    DECLARANT = "Declarant"
    NON_DECLARANT = "Non-Declarant"
    UNKNOWN = "Unknown"


class ResidentialStatus(StrEnum):
    """Residential status reported on historical city and business directories."""

    HOUSEHOLDER = "Householder"
    BOARDER = "Boarder"
    ROOMS = "Rooms"
    TENANT = "Tenant"
    WIDOW = "Widow"
