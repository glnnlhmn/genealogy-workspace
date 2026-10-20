"""Path: src/gda/model/military/draft/colonial.py

Colonial and Revolutionary War militia enrollment and levy record domain entity.

Operational Role:
    Extends MilitaryDraftRecord for pre-1862 conscription, colonial militia musters,
    provincial quotas, and Revolutionary War class levies (1607-1783). Enforces
    militia unit hierarchies, alarm list classifications, and equipment readiness.
"""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.model.atom.id import IndividualID
from gda.model.military.draft.base import DraftCardTier, MilitaryDraftRecord

__version__ = "1.0.0+build.1"

__all__ = ["ColonialMilitiaClass", "ColonialMilitiaRecord", "ColonialWarPeriod"]


class ColonialWarPeriod(StrEnum):
    """Historical conflict or statutory period governing the colonial enrollment."""

    COLONIAL_INTERCOLONIAL = (
        "COLONIAL_INTERCOLONIAL"  # Pre-1754 (King Philip's, Queen Anne's, etc.)
    )
    FRENCH_AND_INDIAN = "FRENCH_AND_INDIAN"  # 1754-1763
    REVOLUTIONARY_WAR = "REVOLUTIONARY_WAR"  # 1775-1783
    EARLY_REPUBLIC = "EARLY_REPUBLIC"  # 1784-1815 (War of 1812 militias)


class ColonialMilitiaClass(StrEnum):
    """Statutory readiness or service classification in colonial militia law."""

    TRAINBAND = "TRAINBAND"  # Standard active defense company (typically ages 16-50/60)
    ALARM_LIST = "ALARM_LIST"  # Secondary home reserve (exempt men, boys, seniors)
    MINUTEMAN = "MINUTEMAN"  # Rapid deployment detachment
    CONTINENTAL_LEVY = (
        "CONTINENTAL_LEVY"  # Drafted to fulfill provincial Continental Line quota
    )
    TOWN_CLASS = "TOWN_CLASS"  # Quota class subdivision assigned to procure a soldier


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class ColonialMilitiaRecord(MilitaryDraftRecord):
    """Evidentiary record for colonial militia enrollments, muster rolls, and levies."""

    conflict_period: ColonialWarPeriod = Field(
        default=ColonialWarPeriod.REVOLUTIONARY_WAR,
        description="Historical conflict era governing the militia roll.",
    )
    militia_class: ColonialMilitiaClass = Field(
        default=ColonialMilitiaClass.TRAINBAND,
        description="Militia organization level or service requirement.",
    )
    colony_or_state_raw: str = Field(
        ...,
        description="Verbatim colony, province, or nascent state (e.g. 'Province of New Hampshire').",
    )
    regiment_verbatim: str | None = Field(
        default=None,
        description="Transcribed regiment name or numerical designation.",
    )
    company_officer_raw: str | None = Field(
        default=None,
        description="Commanding captain or officer under whom the subject enrolled.",
    )
    equipment_readiness_raw: str | None = Field(
        default=None,
        description="Recorded equipment observations (arms, powder, bayonet, knapsack).",
    )
    substitute_provided: bool = Field(
        default=False,
        description="Whether a substitute was furnished for a militia draft or class levy.",
    )
    substitute_individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved IndividualID of the hired substitute if known.",
    )
    substitute_name_raw: str | None = Field(
        default=None,
        description="Transcribed raw name of the substitute provided.",
    )

    VALID_TIERS: ClassVar[set[DraftCardTier]] = {DraftCardTier.OTHER}

    def __post_init__(self) -> None:
        """Enforce pre-1862 historical year boundaries and colonial raw string hygiene."""
        super().__post_init__()

        if not (1607 <= self.draft_year.value <= 1815):
            raise ModelFormatError(
                f"ColonialMilitiaRecord draft_year must be between 1607 and 1815, "
                f"got {self.draft_year.value}."
            )

        colony = self.colony_or_state_raw.strip()
        if not colony:
            raise ModelFormatError(
                "ColonialMilitiaRecord 'colony_or_state_raw' cannot be empty or whitespace.",
                details={"draft_record_id": str(self.draft_record_id)},
            )
        object.__setattr__(self, "colony_or_state_raw", colony)

        if self.substitute_provided and not (
            self.substitute_individual_id
            or (self.substitute_name_raw and self.substitute_name_raw.strip())
        ):
            raise ModelFormatError(
                "ColonialMilitiaRecord requires substitute_name_raw or substitute_individual_id "
                "when substitute_provided is True."
            )
