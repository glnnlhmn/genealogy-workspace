"""Path: src/gda/model/enumerated/__init__.py

Enumerated and tabulated archival source records (census, tax, and directory schedules).
"""

from __future__ import annotations

from gda.core.enums.fiscal import ResidentialStatus, TaxpayerClassification
from gda.model.enumerated.base import EnumeratedRollRecord
from gda.model.enumerated.census import (
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
from gda.model.enumerated.directories import (
    DirectoryEntry,
    DirectoryRollRecord,
)
from gda.model.enumerated.taxes import (
    AssessedProperty,
    SeptennialCensusRecord,
    TaxAssessmentRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "AgriculturalScheduleEntry",
    "AgriculturalScheduleRecord",
    "AssessedProperty",
    "CensusLineEntry",
    "CensusScheduleRecord",
    "DirectoryEntry",
    "DirectoryRollRecord",
    "EnumeratedRollRecord",
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
    "ResidentialStatus",
    "SeptennialCensusRecord",
    "SlaveScheduleEntry",
    "SlaveScheduleRecord",
    "TaxAssessmentRecord",
    "TaxpayerClassification",
    "Veterans1890Entry",
    "Veterans1890ScheduleRecord",
]
