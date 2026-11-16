"""Path: src/gda/model/source/enumerated/census/__init__.py

Federal, state, and special census schedule source models.
"""

from __future__ import annotations

from gda.model.source.enumerated.census.base import (
    CensusLineEntry,
    CensusScheduleRecord,
)
from gda.model.source.enumerated.census.population import (
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
from gda.model.source.enumerated.census.supplemental import (
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
    "AgriculturalScheduleEntry",  # gda.model.source.enumerated.census.supplemental
    "AgriculturalScheduleRecord",  # gda.model.source.enumerated.census.supplemental
    "CensusLineEntry",  # gda.model.source.enumerated.census.base
    "CensusScheduleRecord",  # gda.model.source.enumerated.census.base
    "HouseholdTallyEntry",  # gda.model.source.enumerated.census.population
    "ManufacturingScheduleEntry",  # gda.model.source.enumerated.census.supplemental
    "ManufacturingScheduleRecord",  # gda.model.source.enumerated.census.supplemental
    "MortalityScheduleEntry",  # gda.model.source.enumerated.census.supplemental
    "MortalityScheduleRecord",  # gda.model.source.enumerated.census.supplemental
    "Population1850_1870Entry",  # gda.model.source.enumerated.census.population
    "Population1880Entry",  # gda.model.source.enumerated.census.population
    "Population1900_1910Entry",  # gda.model.source.enumerated.census.population
    "Population1920Entry",  # gda.model.source.enumerated.census.population
    "Population1930Entry",  # gda.model.source.enumerated.census.population
    "Population1940Entry",  # gda.model.source.enumerated.census.population
    "Population1950Entry",  # gda.model.source.enumerated.census.population
    "PopulationLineEntry",  # gda.model.source.enumerated.census.population
    "PopulationSchedule1790_1840",  # gda.model.source.enumerated.census.population
    "PopulationSchedule1850_1870",  # gda.model.source.enumerated.census.population
    "PopulationSchedule1880",  # gda.model.source.enumerated.census.population
    "PopulationSchedule1900_1910",  # gda.model.source.enumerated.census.population
    "PopulationSchedule1920",  # gda.model.source.enumerated.census.population
    "PopulationSchedule1930",  # gda.model.source.enumerated.census.population
    "PopulationSchedule1940",  # gda.model.source.enumerated.census.population
    "PopulationSchedule1950",  # gda.model.source.enumerated.census.population
    "PopulationScheduleRecord",  # gda.model.source.enumerated.census.population
    "SlaveScheduleEntry",  # gda.model.source.enumerated.census.supplemental
    "SlaveScheduleRecord",  # gda.model.source.enumerated.census.supplemental
    "Veterans1890Entry",  # gda.model.source.enumerated.census.supplemental
    "Veterans1890ScheduleRecord",  # gda.model.source.enumerated.census.supplemental
]
