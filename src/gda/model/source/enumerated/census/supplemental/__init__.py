"""Path: src/gda/model/source/enumerated/census/supplemental/__init__.py

Non-population federal census schedule models (mortality, agricultural, manufacturing, slave, veterans).
"""

from __future__ import annotations

from gda.model.source.enumerated.census.supplemental.agricultural import (
    AgriculturalScheduleEntry,
    AgriculturalScheduleRecord,
)
from gda.model.source.enumerated.census.supplemental.manufacturing import (
    ManufacturingScheduleEntry,
    ManufacturingScheduleRecord,
)
from gda.model.source.enumerated.census.supplemental.mortality import (
    MortalityScheduleEntry,
    MortalityScheduleRecord,
)
from gda.model.source.enumerated.census.supplemental.slave import (
    SlaveScheduleEntry,
    SlaveScheduleRecord,
)
from gda.model.source.enumerated.census.supplemental.veterans_1890 import (
    Veterans1890Entry,
    Veterans1890ScheduleRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "AgriculturalScheduleEntry",  # gda.model.source.enumerated.census.supplemental.agricultural
    "AgriculturalScheduleRecord",  # gda.model.source.enumerated.census.supplemental.agricultural
    "ManufacturingScheduleEntry",  # gda.model.source.enumerated.census.supplemental.manufacturing
    "ManufacturingScheduleRecord",  # gda.model.source.enumerated.census.supplemental.manufacturing
    "MortalityScheduleEntry",  # gda.model.source.enumerated.census.supplemental.mortality
    "MortalityScheduleRecord",  # gda.model.source.enumerated.census.supplemental.mortality
    "SlaveScheduleEntry",  # gda.model.source.enumerated.census.supplemental.slave
    "SlaveScheduleRecord",  # gda.model.source.enumerated.census.supplemental.slave
    "Veterans1890Entry",  # gda.model.source.enumerated.census.supplemental.veterans_1890
    "Veterans1890ScheduleRecord",  # gda.model.source.enumerated.census.supplemental.veterans_1890
]
