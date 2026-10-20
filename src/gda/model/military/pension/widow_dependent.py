"""Path: src/gda/model/military/pension/widow_dependent.py

Surviving spouse, minor orphan, and dependent parent pension claim records.

Operational Role:
    Extends MilitaryPensionRecord to represent claims filed by surviving spouses,
    guardians of minor orphans, and dependent parents. Preserves vital proofs
    such as marriage date/place, veteran date of death, and minor child schedules.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.date import HistoricalYear
from gda.model.atom.id import IndividualID, LocationID
from gda.model.military.pension import PensionClaimantRole
from gda.model.military.pension.base import MilitaryPensionRecord

__version__ = "1.0.0+build.2"

__all__ = ["PensionWidowDependentRecord"]


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class PensionWidowDependentRecord(MilitaryPensionRecord):
    """Evidentiary military widow, orphan, or dependent parent pension claim record."""

    veteran_death_year: HistoricalYear | None = Field(
        default=None,
        description="Calendar year of veteran's death cited in the claim.",
    )
    marriage_year: HistoricalYear | None = Field(
        default=None,
        description="Calendar year of marriage between veteran and widow claimant.",
    )
    marriage_location_raw: str | None = Field(
        default=None,
        description="Verbatim location of marriage ceremony cited in supporting proof.",
    )
    marriage_location_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID of the marriage ceremony.",
    )
    remarriage_year: HistoricalYear | None = Field(
        default=None,
        description="Calendar year of widow's remarriage (terminating or modifying pension).",
    )
    guardian_id: IndividualID | None = Field(
        default=None,
        description="Canonical IndividualID of appointed legal guardian for minor orphan claims.",
    )
    guardian_name_raw: str | None = Field(
        default=None,
        description="Verbatim transcribed name of legal guardian executing claim for minors.",
    )
    minor_children_count: int | None = Field(
        default=None,
        ge=0,
        le=25,
        description="Number of minor children under statutory age (e.g. 16) supported by claim.",
    )
    monthly_allowance_usd: float | None = Field(
        default=None,
        ge=0.0,
        description="Monthly pension stipend awarded in USD.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.MILITARY

    def __post_init__(self) -> None:
        """Enforce dependent claimant role boundaries and chronological validity."""
        super().__post_init__()

        valid_roles = {
            PensionClaimantRole.WIDOW,
            PensionClaimantRole.REMARRIED_WIDOW,
            PensionClaimantRole.MINOR_CHILD,
            PensionClaimantRole.DEPENDENT_PARENT,
            PensionClaimantRole.OTHER_DEPENDENT,
        }
        if self.claimant_role not in valid_roles:
            raise ModelFormatError(
                f"PensionWidowDependentRecord requires claimant_role in "
                f"{sorted(r.value for r in valid_roles)}, got '{self.claimant_role.value}'."
            )

        if self.marriage_year and self.veteran_death_year:
            if self.veteran_death_year.value < self.marriage_year.value:
                raise ModelFormatError(
                    f"veteran_death_year ({self.veteran_death_year.value}) cannot precede "
                    f"marriage_year ({self.marriage_year.value})."
                )

        if self.remarriage_year and self.marriage_year:
            if self.remarriage_year.value < self.marriage_year.value:
                raise ModelFormatError(
                    f"remarriage_year ({self.remarriage_year.value}) cannot precede "
                    f"marriage_year ({self.marriage_year.value})."
                )
