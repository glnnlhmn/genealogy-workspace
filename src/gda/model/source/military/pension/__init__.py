"""Path: src/gda/model/source/military/pension/__init__.py

Military pension applications, invalid disability claims, widow/dependent files,
and bounty land warrant records across historical conflicts.
"""

from __future__ import annotations

from gda.core.enums.military import (
    BountyLandAct,
    PensionClaimantRole,
    PensionPaymentAuthority,
)
from gda.model.source.military.pension.base import MilitaryPensionRecord
from gda.model.source.military.pension.bounty_land import BountyLandWarrantRecord
from gda.model.source.military.pension.veteran_claim import PensionVeteranClaimRecord
from gda.model.source.military.pension.widow_dependent import PensionWidowDependentRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "BountyLandAct",  # gda.core.enums.military
    "BountyLandWarrantRecord",  # gda.model.source.military.pension.bounty_land
    "MilitaryPensionRecord",  # gda.model.source.military.pension.base
    "PensionClaimantRole",  # gda.core.enums.military
    "PensionPaymentAuthority",  # gda.core.enums.military
    "PensionVeteranClaimRecord",  # gda.model.source.military.pension.veteran_claim
    "PensionWidowDependentRecord",  # gda.model.source.military.pension.widow_dependent
]
