"""Path: src/gda/model/military/pension/__init__.py

Military pension applications, invalid disability claims, widow/dependent files,
and bounty land warrant records across historical conflicts.
"""

from __future__ import annotations

from gda.core.enums.military import (
    BountyLandAct,
    PensionClaimantRole,
    PensionPaymentAuthority,
)
from gda.model.military.pension.base import MilitaryPensionRecord
from gda.model.military.pension.bounty_land import BountyLandWarrantRecord
from gda.model.military.pension.veteran_claim import PensionVeteranClaimRecord
from gda.model.military.pension.widow_dependent import PensionWidowDependentRecord

__version__ = "2.1.0+build.1"

__all__ = [
    "BountyLandAct",
    "BountyLandWarrantRecord",
    "MilitaryPensionRecord",
    "PensionClaimantRole",
    "PensionPaymentAuthority",
    "PensionVeteranClaimRecord",
    "PensionWidowDependentRecord",
]
