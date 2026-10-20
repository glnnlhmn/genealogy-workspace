"""Path: src/gda/model/military/pension/__init__.py

Military pension applications, invalid disability claims, widow/dependent files,
and bounty land warrant records across historical conflicts.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.0.0+build.4"

__all__ = [
    "BountyLandAct",
    "BountyLandWarrantRecord",
    "MilitaryPensionRecord",
    "PensionClaimantRole",
    "PensionPaymentAuthority",
    "PensionVeteranClaimRecord",
    "PensionWidowDependentRecord",
]


class PensionClaimantRole(StrEnum):
    """Relationship of the pension claimant to the veteran."""

    VETERAN = "VETERAN"
    WIDOW = "WIDOW"
    REMARRIED_WIDOW = "REMARRIED_WIDOW"
    MINOR_CHILD = "MINOR_CHILD"
    DEPENDENT_PARENT = "DEPENDENT_PARENT"
    OTHER_DEPENDENT = "OTHER_DEPENDENT"


class PensionPaymentAuthority(StrEnum):
    """Statutory or administrative authority governing pension disbursement."""

    US_BUREAU_OF_PENSIONS = "US_BUREAU_OF_PENSIONS"
    US_VETERANS_ADMINISTRATION = "US_VETERANS_ADMINISTRATION"
    CONTINENTAL_CONGRESS = "CONTINENTAL_CONGRESS"
    CONFEDERATE_STATE = "CONFEDERATE_STATE"
    STATE_PENSION_BOARD = "STATE_PENSION_BOARD"
    COLONIAL_ASSEMBLY = "COLONIAL_ASSEMBLY"
    OTHER = "OTHER"


class BountyLandAct(StrEnum):
    """Congressional acts authorizing military bounty land warrant grants."""

    REVOLUTIONARY_WAR_ACTS = "REVOLUTIONARY_WAR_ACTS"
    ACT_OF_1812 = "ACT_OF_1812"
    ACT_OF_1850 = "ACT_OF_1850"
    ACT_OF_1852 = "ACT_OF_1852"
    ACT_OF_1855 = "ACT_OF_1855"
    STATE_MILITARY_DISTRICT = "STATE_MILITARY_DISTRICT"
    OTHER = "OTHER"


# Downstream domain model imports
from gda.model.military.pension.base import MilitaryPensionRecord  # noqa: E402
from gda.model.military.pension.bounty_land import BountyLandWarrantRecord  # noqa: E402
from gda.model.military.pension.veteran_claim import PensionVeteranClaimRecord  # noqa: E402
from gda.model.military.pension.widow_dependent import PensionWidowDependentRecord  # noqa: E402
