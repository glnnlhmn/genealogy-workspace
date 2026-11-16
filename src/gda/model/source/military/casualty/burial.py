"""Path: src/gda/model/source/military/casualty/burial.py

Military cemetery interments, national cemeteries, and government headstones.

Operational Role:
    Extends MilitaryCasualtyRecord to represent military interments, national
    cemetery registrations, American Battle Monuments Commission (ABMC) burials,
    and applications for government military headstones/markers.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.military import CasualtyCategory, IntermentCemeteryType
from gda.core.errors import ModelFormatError
from gda.model.atom.id import LocationID
from gda.model.atom.year import HistoricalYear
from gda.model.source.military.casualty.base import MilitaryCasualtyRecord

__version__ = "1.0.0+build.1"

__all__ = ["MilitaryBurialRecord"]

_BURIAL_CATEGORIES: frozenset[CasualtyCategory] = frozenset(
    {
        CasualtyCategory.KILLED_IN_ACTION,
        CasualtyCategory.DIED_OF_WOUNDS,
        CasualtyCategory.DIED_OF_DISEASE,
        CasualtyCategory.DIED_IN_SERVICE,
        CasualtyCategory.NON_COMBAT_DEATH,
    }
)


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class MilitaryBurialRecord(MilitaryCasualtyRecord):
    """Evidentiary military interment or headstone registration record."""

    cemetery_type: IntermentCemeteryType = Field(
        ...,
        description="Jurisdiction or type of cemetery (e.g. NATIONAL_CEMETERY, ABMC_OVERSEAS).",
    )
    cemetery_name_raw: str = Field(
        ...,
        description="Verbatim name of cemetery or memorial grounds.",
    )
    interment_year: HistoricalYear = Field(
        ...,
        description="Calendar year the servicemember was interred or memorialized.",
    )
    plot_section_raw: str | None = Field(
        default=None,
        description="Verbatim section, lot, and grave number (e.g. 'Section 60, Grave 1402').",
    )
    headstone_type_raw: str | None = Field(
        default=None,
        description="Verbatim headstone specification (e.g. 'Upright Marble', 'Bronze Niche').",
    )
    cemetery_location_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID of the cemetery.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[CasualtyCategory]] = _BURIAL_CATEGORIES

    def __post_init__(self) -> None:
        """Enforce burial category constraints and text hygiene."""
        super().__post_init__()

        if self.casualty_category not in self.ALLOWED_CATEGORIES:
            raise ModelFormatError(
                f"MilitaryBurialRecord requires deceased casualty_category in "
                f"{sorted(c.value for c in self.ALLOWED_CATEGORIES)}, got '{self.casualty_category.value}'."
            )

        cem = self.cemetery_name_raw.strip()
        if not cem:
            raise ModelFormatError(
                "MilitaryBurialRecord 'cemetery_name_raw' cannot be empty or whitespace."
            )
        if cem != self.cemetery_name_raw:
            object.__setattr__(self, "cemetery_name_raw", cem)

        if self.plot_section_raw is not None:
            plt = self.plot_section_raw.strip()
            if not plt:
                raise ModelFormatError(
                    "MilitaryBurialRecord 'plot_section_raw' cannot be empty or whitespace."
                )
            if plt != self.plot_section_raw:
                object.__setattr__(self, "plot_section_raw", plt)

        if self.interment_year.value < self.casualty_year.value:
            raise ModelFormatError(
                f"interment_year ({self.interment_year.value}) cannot precede "
                f"casualty_year ({self.casualty_year.value})."
            )
