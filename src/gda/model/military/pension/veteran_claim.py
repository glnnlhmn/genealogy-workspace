"""Path: src/gda/model/military/pension/veteran_claim.py

Invalid veteran disability and service pension claim records.

Operational Role:
    Extends MilitaryPensionRecord to represent invalid veteran disability claims,
    monthly stipend amounts, physical disability descriptions, and medical board
    examination ratings.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.sources import SourceRecordCategory
from gda.model.military.pension import PensionClaimantRole
from gda.model.military.pension.base import MilitaryPensionRecord

__version__ = "1.0.0+build.1"

__all__ = ["PensionVeteranClaimRecord"]


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class PensionVeteranClaimRecord(MilitaryPensionRecord):
    """Evidentiary invalid veteran disability or service pension claim record."""

    disability_description_raw: str | None = Field(
        default=None,
        description="Verbatim physical injury, illness, or disability cited in claim.",
    )
    monthly_allowance_usd: float | None = Field(
        default=None,
        ge=0.0,
        description="Monthly pension stipend amount awarded in USD.",
    )
    disability_rating_percentage: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Medical board or Bureau of Pensions disability evaluation percentage.",
    )
    examining_surgeon_raw: str | None = Field(
        default=None,
        description="Verbatim name or board of examining surgeons conducting physical exam.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.MILITARY

    def __post_init__(self) -> None:
        """Enforce veteran claimant role integrity."""
        super().__post_init__()

        if self.claimant_role != PensionClaimantRole.VETERAN:
            raise ModelFormatError(
                f"PensionVeteranClaimRecord requires claimant_role 'VETERAN', "
                f"got '{self.claimant_role.value}'."
            )
