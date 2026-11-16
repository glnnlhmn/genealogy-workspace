"""Path: src/gda/model/source/enumerated/__init__.py

Enumerated and tabulated archival source records (census, tax, and directory schedules).
"""

from __future__ import annotations

from gda.core.enums.fiscal import ResidentialStatus, TaxpayerClassification
from gda.model.source.enumerated.base import EnumeratedRollRecord
from gda.model.source.enumerated.census import (
    AgriculturalScheduleEntry,
    AgriculturalScheduleRecord,
    CensusLineEntry,
    CensusScheduleRecord,
    HouseholdTallyEntry,
    ManufacturingScheduleEntry,
    ManufacturingScheduleRecord,
    MortalityScheduleEntry,
    MortalityScheduleRecord,
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
    SlaveScheduleEntry,
    SlaveScheduleRecord,
    Veterans1890Entry,
    Veterans1890ScheduleRecord,
)
from gda.model.source.enumerated.directories import (
    DirectoryEntry,
    DirectoryRollRecord,
)
from gda.model.source.enumerated.taxes import (
    AssessedProperty,
    SeptennialCensusRecord,
    TaxAssessmentRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "AgriculturalScheduleEntry",  # gda.model.source.enumerated.census
    "AgriculturalScheduleRecord",  # gda.model.source.enumerated.census
    "AssessedProperty",  # gda.model.source.enumerated.taxes
    "CensusLineEntry",  # gda.model.source.enumerated.census
    "CensusScheduleRecord",  # gda.model.source.enumerated.census
    "DirectoryEntry",  # gda.model.source.enumerated.directories
    "DirectoryRollRecord",  # gda.model.source.enumerated.directories
    "EnumeratedRollRecord",  # gda.model.source.enumerated.base
    "HouseholdTallyEntry",  # gda.model.source.enumerated.census
    "ManufacturingScheduleEntry",  # gda.model.source.enumerated.census
    "ManufacturingScheduleRecord",  # gda.model.source.enumerated.census
    "MortalityScheduleEntry",  # gda.model.source.enumerated.census
    "MortalityScheduleRecord",  # gda.model.source.enumerated.census
    "Population1850_1870Entry",  # gda.model.source.enumerated.census
    "Population1880Entry",  # gda.model.source.enumerated.census
    "Population1900_1910Entry",  # gda.model.source.enumerated.census
    "Population1920Entry",  # gda.model.source.enumerated.census
    "Population1930Entry",  # gda.model.source.enumerated.census
    "Population1940Entry",  # gda.model.source.enumerated.census
    "Population1950Entry",  # gda.model.source.enumerated.census
    "PopulationLineEntry",  # gda.model.source.enumerated.census
    "PopulationSchedule1790_1840",  # gda.model.source.enumerated.census
    "PopulationSchedule1850_1870",  # gda.model.source.enumerated.census
    "PopulationSchedule1880",  # gda.model.source.enumerated.census
    "PopulationSchedule1900_1910",  # gda.model.source.enumerated.census
    "PopulationSchedule1920",  # gda.model.source.enumerated.census
    "PopulationSchedule1930",  # gda.model.source.enumerated.census
    "PopulationSchedule1940",  # gda.model.source.enumerated.census
    "PopulationSchedule1950",  # gda.model.source.enumerated.census
    "PopulationScheduleRecord",  # gda.model.source.enumerated.census
    "ResidentialStatus",  # gda.core.enums.fiscal
    "SeptennialCensusRecord",  # gda.model.source.enumerated.taxes
    "SlaveScheduleEntry",  # gda.model.source.enumerated.census
    "SlaveScheduleRecord",  # gda.model.source.enumerated.census
    "TaxAssessmentRecord",  # gda.model.source.enumerated.taxes
    "TaxpayerClassification",  # gda.core.enums.fiscal
    "Veterans1890Entry",  # gda.model.source.enumerated.census
    "Veterans1890ScheduleRecord",  # gda.model.source.enumerated.census
]
