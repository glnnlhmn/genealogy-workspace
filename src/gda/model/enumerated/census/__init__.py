"""Path: src/gda/model/enumerated/census/__init__.py

Federal, state, and special census schedule source models.
"""

from __future__ import annotations

from gda.model.enumerated.census.base import (
    CensusLineEntry,
    CensusScheduleRecord,
)
from gda.model.enumerated.census.population import (
    HouseholdTallyEntry,
    Population1850_1870Entry,
    Population1880Entry,
    Population1900_1910Entry,
    Population1920Entry,
    Population1930Entry,
    Population1940Entry,
    Population1950Entry,
    PopulationLineEntry,
    PopulationSchedule1790_1840,
    PopulationSchedule1850_1870,
    PopulationSchedule1880,
    PopulationSchedule1900_1910,
    PopulationSchedule1920,
    PopulationSchedule1930,
    PopulationSchedule1940,
    PopulationSchedule1950,
    PopulationScheduleRecord,
)
from gda.model.enumerated.census.supplemental import (
    AgriculturalScheduleEntry,
    AgriculturalScheduleRecord,
    ManufacturingScheduleEntry,
    ManufacturingScheduleRecord,
    MortalityScheduleEntry,
    MortalityScheduleRecord,
    SlaveScheduleEntry,
    SlaveScheduleRecord,
    Veterans1890Entry,
    Veterans1890ScheduleRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "AgriculturalScheduleEntry",
    "AgriculturalScheduleRecord",
    "CensusLineEntry",
    "CensusScheduleRecord",
    "HouseholdTallyEntry",
    "ManufacturingScheduleEntry",
    "ManufacturingScheduleRecord",
    "MortalityScheduleEntry",
    "MortalityScheduleRecord",
    "Population1850_1870Entry",
    "Population1880Entry",
    "Population1900_1910Entry",
    "Population1920Entry",
    "Population1930Entry",
    "Population1940Entry",
    "Population1950Entry",
    "PopulationLineEntry",
    "PopulationSchedule1790_1840",
    "PopulationSchedule1850_1870",
    "PopulationSchedule1880",
    "PopulationSchedule1900_1910",
    "PopulationSchedule1920",
    "PopulationSchedule1930",
    "PopulationSchedule1940",
    "PopulationSchedule1950",
    "PopulationScheduleRecord",
    "SlaveScheduleEntry",
    "SlaveScheduleRecord",
    "Veterans1890Entry",
    "Veterans1890ScheduleRecord",
]
