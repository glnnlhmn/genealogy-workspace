"""Path: src/gda/model/military/casualty/combat.py

Battlefield combat casualty records (KIA, WIA, DOW, MIA).

Operational Role:
    Extends MilitaryCasualtyRecord to capture battlefield engagement details,
    wounding causes, artillery/small-arms trauma, and aid station evacuations.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.date import HistoricalYear
from gda.model.atom.id import LocationID
from gda.model.military.casualty import CasualtyCategory
from gda.model.military.casualty.base import MilitaryCasualtyRecord

__version__ = "1.0.0+build.1"

__all__ = ["CombatCasualtyRecord"]


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class CombatCasualtyRecord(MilitaryCasualtyRecord):
    """Evidentiary combat battlefield casualty entry."""

    engagement_name_raw: str | None = Field(
        default=None,
        description="Verbatim named battle, assault, action, or operation.",
    )
    cause_of_casualty_raw: str | None = Field(
        default=None,
        description="Verbatim weapon, ordnance, or cause (e.g. 'Gunshot wound', 'Artillery shell').",
    )
    aid_station_raw: str | None = Field(
        default=None,
        description="Verbatim field hospital, dressing station, or hospital ship.",
    )
    died_of_wounds_year: HistoricalYear | None = Field(
        default=None,
        description="Calendar year of death if wounded soldier subsequently died of wounds (DOW).",
    )
    evacuation_location_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID of receiving evacuation hospital.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.MILITARY

    def __post_init__(self) -> None:
        """Enforce combat casualty category constraints and chronology."""
        super().__post_init__()

        combat_categories = {
            CasualtyCategory.KILLED_IN_ACTION,
            CasualtyCategory.DIED_OF_WOUNDS,
            CasualtyCategory.WOUNDED_IN_ACTION,
            CasualtyCategory.MISSING_IN_ACTION,
            CasualtyCategory.DIED_OF_DISEASE,
        }
        if self.casualty_category not in combat_categories:
            raise ModelFormatError(
                f"CombatCasualtyRecord requires combat casualty_category in "
                f"{sorted(c.value for c in combat_categories)}, got '{self.casualty_category.value}'."
            )

        if self.died_of_wounds_year is not None:
            if self.died_of_wounds_year.value < self.casualty_year.value:
                raise ModelFormatError(
                    f"died_of_wounds_year ({self.died_of_wounds_year.value}) cannot precede "
                    f"casualty_year ({self.casualty_year.value})."
                )

        if self.engagement_name_raw is not None:
            eng = self.engagement_name_raw.strip()
            if not eng:
                raise ModelFormatError(
                    "CombatCasualtyRecord 'engagement_name_raw' cannot be empty or whitespace."
                )
            object.__setattr__(self, "engagement_name_raw", eng)
