"""Path: src/gda/model/source/enumerated/taxes/__init__.py

Historical tax assessment rolls, septennial censuses, and freemen/exoneration lists.
"""

from __future__ import annotations

from gda.core.enums.fiscal import TaxpayerClassification
from gda.model.source.enumerated.taxes.base import (
    AssessedProperty,
    TaxAssessmentRecord,
)
from gda.model.source.enumerated.taxes.septennial import SeptennialCensusRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "AssessedProperty",  # gda.model.source.enumerated.taxes.base
    "SeptennialCensusRecord",  # gda.model.source.enumerated.taxes.septennial
    "TaxAssessmentRecord",  # gda.model.source.enumerated.taxes.base
    "TaxpayerClassification",  # gda.core.enums.fiscal
]
