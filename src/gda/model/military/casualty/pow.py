"""Path: src/gda/model/military/casualty/pow.py

Prisoner of War (POW) internment, detention, and repatriation records.

Operational Role:
    Extends MilitaryCasualtyRecord to capture POW status, detaining power,
    prison camp facilities, capture dates, and release/death in captivity.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.date import HistoricalYear
from gda.model.atom.id import LocationID
from gda.model.military.casualty import CasualtyCategory, PowCampType
from gda.model.military.casualty.base import MilitaryCasualtyRecord

__version__ = "1.0.0+build.1"

__all__ = ["PrisonerOfWarRecord"]


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class PrisonerOfWarRecord(MilitaryCasualtyRecord):
    """Evidentiary military prisoner of war internment record."""

    camp_type: PowCampType = Field(
        ...,
        description="Administrative category or branch of POW detention camp.",
    )
    camp_name_raw: str = Field(
        ...,
        description="Verbatim name or designation of prison camp (e.g. 'Stalag Luft III', 'Andersonville').",
    )
    detaining_power_raw: str = Field(
        ...,
        description="Verbatim nation, belligerent power, or army holding the prisoner.",
    )
    capture_year: HistoricalYear = Field(
        ...,
        description="Calendar year servicemember was taken prisoner.",
    )
    release_or_repatriation_year: HistoricalYear | None = Field(
        default=None,
        description="Calendar year soldier was exchanged, repatriated, or escaped.",
    )
    died_in_captivity: bool = Field(
        default=False,
        description="Flag indicating servicemember died while interned as a prisoner of war.",
    )
    camp_location_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID of the prison camp.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.MILITARY

    def __post_init__(self) -> None:
        """Enforce prisoner of war category and chronological detention order."""
        super().__post_init__()

        if self.casualty_category != CasualtyCategory.PRISONER_OF_WAR:
            raise ModelFormatError(
                f"PrisonerOfWarRecord requires casualty_category 'PRISONER_OF_WAR', "
                f"got '{self.casualty_category.value}'."
            )

        c_name = self.camp_name_raw.strip()
        if not c_name:
            raise ModelFormatError(
                "PrisonerOfWarRecord 'camp_name_raw' cannot be empty or whitespace."
            )
        object.__setattr__(self, "camp_name_raw", c_name)

        pwr = self.detaining_power_raw.strip()
        if not pwr:
            raise ModelFormatError(
                "PrisonerOfWarRecord 'detaining_power_raw' cannot be empty or whitespace."
            )
        object.__setattr__(self, "detaining_power_raw", pwr)

        if self.release_or_repatriation_year is not None:
            if self.release_or_repatriation_year.value < self.capture_year.value:
                raise ModelFormatError(
                    f"release_or_repatriation_year ({self.release_or_repatriation_year.value}) "
                    f"cannot precede capture_year ({self.capture_year.value})."
                )
