"""Path: src/gda/core/enums/land.py

Real-property conveyance party roles and public-domain land grant basis enums.

Operational Role:
    Defines controlled categorical enumerations for grantor/grantee capacities on
    deeds and statutory/proprietary bases for sovereign land patents and warrants.
"""

from __future__ import annotations

from gda.core.enums.base import GDAStrEnum

__version__ = "1.0.0+build.2"

__all__ = [
    "DeedPartyRole",
    "LandGrantBasis",
]


class DeedPartyRole(GDAStrEnum):
    """Conveyance capacity of a party named in a deed or real-property instrument."""

    GRANTOR = "GRANTOR"
    GRANTEE = "GRANTEE"


class LandGrantBasis(GDAStrEnum):
    """Statutory or customary basis for sovereign land patents, warrants, and grants."""

    CASH_ENTRY = "CASH_ENTRY"
    HOMESTEAD = "HOMESTEAD"
    BOUNTY_LAND = "BOUNTY_LAND"
    PREEMPTION = "PREEMPTION"
    PROPRIETARY_GRANT = "PROPRIETARY_GRANT"
    OTHER = "OTHER"
