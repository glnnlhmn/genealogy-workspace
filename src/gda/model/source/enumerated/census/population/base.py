"""Path: src/gda/model/source/enumerated/census/population/base.py

Base population schedule domain models for decennial population enumerations.

Operational Role:
    Specializes CensusScheduleRecord for SourceRecordType.POPULATION_SCHEDULE
    and defines shared household/individual visitation line entry primitives.
"""

from __future__ import annotations

from typing import ClassVar, TypeVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.sources import SourceRecordType
from gda.model.source.enumerated.census.base import CensusLineEntry, CensusScheduleRecord

__version__ = "1.0.0+build.2"

__all__ = [
    "PopulationLineEntry",
    "PopulationScheduleRecord",
    "TPopEntry",
]


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class PopulationLineEntry(CensusLineEntry):
    """Base enumerated line entry for decennial population schedules."""

    dwelling_number: str | None = Field(
        default=None,
        description="Dwelling-house visitation sequence number.",
    )
    family_number: str | None = Field(
        default=None,
        description="Family/household visitation sequence number.",
    )


TPopEntry = TypeVar("TPopEntry", bound=PopulationLineEntry)


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class PopulationScheduleRecord[TEntry: PopulationLineEntry](CensusScheduleRecord[TEntry]):
    """Evidentiary composite for decennial census Population Schedules."""

    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = frozenset(
        {SourceRecordType.POPULATION_SCHEDULE}
    )
