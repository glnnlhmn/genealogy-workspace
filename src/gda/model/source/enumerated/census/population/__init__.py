"""Path: src/gda/model/source/enumerated/census/population/__init__.py

Decennial U.S. Federal Population Schedule models across historical eras (1790-1950).
"""

from __future__ import annotations

from gda.model.source.enumerated.census.population.base import (
    PopulationLineEntry,
    PopulationScheduleRecord,
)
from gda.model.source.enumerated.census.population.schedule_1850_1870 import (
    Population1850_1870Entry,
    PopulationSchedule1850_1870,
)
from gda.model.source.enumerated.census.population.schedule_1880 import (
    Population1880Entry,
    PopulationSchedule1880,
)
from gda.model.source.enumerated.census.population.schedule_1900_1910 import (
    Population1900_1910Entry,
    PopulationSchedule1900_1910,
)
from gda.model.source.enumerated.census.population.schedule_1920 import (
    Population1920Entry,
    PopulationSchedule1920,
)
from gda.model.source.enumerated.census.population.schedule_1930 import (
    Population1930Entry,
    PopulationSchedule1930,
)
from gda.model.source.enumerated.census.population.schedule_1940 import (
    Population1940Entry,
    PopulationSchedule1940,
)
from gda.model.source.enumerated.census.population.schedule_1950 import (
    Population1950Entry,
    PopulationSchedule1950,
)
from gda.model.source.enumerated.census.population.tally_1790_1840 import (
    HouseholdTallyEntry,
    PopulationSchedule1790_1840,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "HouseholdTallyEntry",  # gda.model.source.enumerated.census.population.tally_1790_1840
    "Population1850_1870Entry",  # gda.model.source.enumerated.census.population.schedule_1850_1870
    "Population1880Entry",  # gda.model.source.enumerated.census.population.schedule_1880
    "Population1900_1910Entry",  # gda.model.source.enumerated.census.population.schedule_1900_1910
    "Population1920Entry",  # gda.model.source.enumerated.census.population.schedule_1920
    "Population1930Entry",  # gda.model.source.enumerated.census.population.schedule_1930
    "Population1940Entry",  # gda.model.source.enumerated.census.population.schedule_1940
    "Population1950Entry",  # gda.model.source.enumerated.census.population.schedule_1950
    "PopulationLineEntry",  # gda.model.source.enumerated.census.population.base
    "PopulationSchedule1790_1840",  # gda.model.source.enumerated.census.population.tally_1790_1840
    "PopulationSchedule1850_1870",  # gda.model.source.enumerated.census.population.schedule_1850_1870
    "PopulationSchedule1880",  # gda.model.source.enumerated.census.population.schedule_1880
    "PopulationSchedule1900_1910",  # gda.model.source.enumerated.census.population.schedule_1900_1910
    "PopulationSchedule1920",  # gda.model.source.enumerated.census.population.schedule_1920
    "PopulationSchedule1930",  # gda.model.source.enumerated.census.population.schedule_1930
    "PopulationSchedule1940",  # gda.model.source.enumerated.census.population.schedule_1940
    "PopulationSchedule1950",  # gda.model.source.enumerated.census.population.schedule_1950
    "PopulationScheduleRecord",  # gda.model.source.enumerated.census.population.base
]
