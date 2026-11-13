"""Path: src/gda/model/enumerated/taxes/__init__.py

Historical tax assessment rolls, septennial censuses, and freemen/exoneration lists.
"""

from __future__ import annotations

from gda.core.enums.fiscal import TaxpayerClassification
from gda.model.enumerated.taxes.base import (
    AssessedProperty,
    TaxAssessmentRecord,
)
from gda.model.enumerated.taxes.septennial import SeptennialCensusRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "AssessedProperty",
    "SeptennialCensusRecord",
    "TaxAssessmentRecord",
    "TaxpayerClassification",
]
