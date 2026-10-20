"""Path: src/gda/model/military/casualty/base.py

Foundational military casualty domain entity model.

Operational Role:
    Extends SourceRecord composite to represent military casualty reports,
    hospital registers, notification telegrams, and historical casualty rolls
    across conflicts, branches, and theaters of operations.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.date import HistoricalYear
from gda.model.atom.id import IndividualID, LocationID, TranscriptID
from gda.model.base.source_record import SourceRecord
from gda.model.military.casualty import CasualtyCategory
from gda.model.military.service import MilitaryBranch

__version__ = "1.0.0+build.1"

__all__ = ["MilitaryCasualtyRecord"]


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class MilitaryCasualtyRecord(SourceRecord):
    """Evidentiary military casualty notification or report entry."""

    servicemember_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the affected servicemember.",
    )
    servicemember_name_raw: str = Field(
        ...,
        description="Verbatim transcribed name of the casualty from the report.",
    )
    branch: MilitaryBranch = Field(
        ...,
        description="Armed branch in which the casualty occurred.",
    )
    casualty_category: CasualtyCategory = Field(
        ...,
        description="Primary casualty classification (e.g. KILLED_IN_ACTION, WOUNDED).",
    )
    casualty_year: HistoricalYear = Field(
        ...,
        description="Calendar year the casualty event occurred.",
    )
    unit_designation_raw: str = Field(
        ...,
        description="Verbatim military unit, ship, or squadron to which servicemember was attached.",
    )
    rank_raw: str = Field(
        ...,
        description="Verbatim military rank or rating held at time of casualty.",
    )
    service_number_raw: str | None = Field(
        default=None,
        description="Military serial or service number if recorded on report.",
    )
    theater_of_operations_raw: str | None = Field(
        default=None,
        description="Verbatim theater of war or operational area (e.g. European Theater, PTO).",
    )
    casualty_location_raw: str | None = Field(
        default=None,
        description="Verbatim geographical location, sector, or grid of casualty event.",
    )
    casualty_location_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID of casualty event.",
    )
    transcript_id: TranscriptID | None = Field(
        default=None,
        description="Decoupled TranscriptID linking casualty telegram or narrative extract.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.MILITARY

    def __post_init__(self) -> None:
        """Enforce domain category and raw string sanitation."""
        super().__post_init__()

        if self.record_category != self.EXPECTED_CATEGORY:
            raise ModelFormatError(
                f"MilitaryCasualtyRecord requires category '{self.EXPECTED_CATEGORY.value}', "
                f"got '{self.record_category.value}'."
            )

        name = self.servicemember_name_raw.strip()
        if not name:
            raise ModelFormatError(
                "MilitaryCasualtyRecord 'servicemember_name_raw' cannot be empty or whitespace."
            )
        object.__setattr__(self, "servicemember_name_raw", name)

        unit = self.unit_designation_raw.strip()
        if not unit:
            raise ModelFormatError(
                "MilitaryCasualtyRecord 'unit_designation_raw' cannot be empty or whitespace."
            )
        object.__setattr__(self, "unit_designation_raw", unit)

        rank = self.rank_raw.strip()
        if not rank:
            raise ModelFormatError(
                "MilitaryCasualtyRecord 'rank_raw' cannot be empty or whitespace."
            )
        object.__setattr__(self, "rank_raw", rank)

        if self.service_number_raw is not None:
            s_num = self.service_number_raw.strip()
            if not s_num:
                raise ModelFormatError(
                    "MilitaryCasualtyRecord 'service_number_raw' cannot be empty or whitespace."
                )
            object.__setattr__(self, "service_number_raw", s_num)

        if self.casualty_location_raw is not None:
            c_loc = self.casualty_location_raw.strip()
            if not c_loc:
                raise ModelFormatError(
                    "MilitaryCasualtyRecord 'casualty_location_raw' cannot be empty or whitespace."
                )
            object.__setattr__(self, "casualty_location_raw", c_loc)

    def __str__(self) -> str:
        return (
            f"MilitaryCasualtyRecord [{self.casualty_category.value}] {self.rank_raw} "
            f"{self.servicemember_name_raw} - {self.unit_designation_raw} "
            f"({self.casualty_year.value})"
        )
