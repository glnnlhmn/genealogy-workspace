"""Path: src/gda/model/source/enumerated/census/supplemental/slave.py

Federal Census Slave Schedule domain models (1850 & 1860).

Operational Role:
    Models Schedule 2 (Slave Inhabitants) entries for 1850 and 1860, linking
    slaveholder names/IDs and individual enslaved person line entries.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.sources import SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.types import US_SLAVE_SCHEDULE_YEARS
from gda.model.atom.id import IndividualID
from gda.model.source.enumerated.census.base import CensusLineEntry, CensusScheduleRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "SlaveScheduleEntry",
    "SlaveScheduleRecord",
]


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class SlaveScheduleEntry(CensusLineEntry):
    """Line entry on a 1850 or 1860 Federal Slave Schedule."""

    slaveholder_name_raw: str = Field(
        ..., description="Verbatim name of the slaveholder or employer on the schedule."
    )
    slaveholder_id: IndividualID | None = Field(
        default=None, description="Resolved IndividualID of the slaveholder."
    )
    color_raw: str | None = Field(default=None, description="Verbatim color notation ('B' or 'M').")
    fugitive_from_state: bool = Field(
        default=False, description="Flag indicating person recorded as fugitive from the state."
    )
    number_manumitted: int | None = Field(
        default=None, ge=0, description="Number manumitted during the census year."
    )
    slave_houses_count: int | None = Field(
        default=None, ge=0, description="Number of slave houses recorded (1860 schedule)."
    )

    def __post_init__(self) -> None:
        """Enforce non-empty slaveholder_name_raw hygiene."""
        super().__post_init__()

        holder = self.slaveholder_name_raw.strip()
        if not holder:
            raise ModelFormatError(
                "SlaveScheduleEntry 'slaveholder_name_raw' cannot be empty or whitespace.",
                details={"entry_urn": str(self.entry_urn)},
            )
        if holder != self.slaveholder_name_raw:
            object.__setattr__(self, "slaveholder_name_raw", holder)


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class SlaveScheduleRecord(CensusScheduleRecord[SlaveScheduleEntry]):
    """Evidentiary composite for 1850 and 1860 Federal Slave Schedules."""

    record_type: SourceRecordType = Field(
        default=SourceRecordType.SLAVE_SCHEDULE,
        description="Fixed SLAVE_SCHEDULE source record type.",
    )

    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = frozenset(
        {SourceRecordType.SLAVE_SCHEDULE}
    )

    def __post_init__(self) -> None:
        """Enforce 1850 or 1860 slave schedule year boundaries."""
        super().__post_init__()

        if self.enumeration_year.value not in US_SLAVE_SCHEDULE_YEARS:
            raise ModelFormatError(
                f"SlaveScheduleRecord enumeration_year must be in "
                f"{sorted(US_SLAVE_SCHEDULE_YEARS)}, got {self.enumeration_year.value}."
            )
