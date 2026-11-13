"""Path: src/gda/model/enumerated/census/supplemental/__init__.py

Non-population federal census schedule models (mortality, agricultural, manufacturing, slave, veterans).
"""

from __future__ import annotations

from gda.model.enumerated.census.supplemental.agricultural import (
    AgriculturalScheduleEntry,
    AgriculturalScheduleRecord,
)
from gda.model.enumerated.census.supplemental.manufacturing import (
    ManufacturingScheduleEntry,
    ManufacturingScheduleRecord,
)
from gda.model.enumerated.census.supplemental.mortality import (
    MortalityScheduleEntry,
    MortalityScheduleRecord,
)
from gda.model.enumerated.census.supplemental.slave import (
    SlaveScheduleEntry,
    SlaveScheduleRecord,
)
from gda.model.enumerated.census.supplemental.veterans_1890 import (
    Veterans1890Entry,
    Veterans1890ScheduleRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "AgriculturalScheduleEntry",
    "AgriculturalScheduleRecord",
    "ManufacturingScheduleEntry",
    "ManufacturingScheduleRecord",
    "MortalityScheduleEntry",
    "MortalityScheduleRecord",
    "SlaveScheduleEntry",
    "SlaveScheduleRecord",
    "Veterans1890Entry",
    "Veterans1890ScheduleRecord",
]
