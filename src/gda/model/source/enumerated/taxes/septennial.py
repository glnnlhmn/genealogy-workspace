"""Path: src/gda/model/source/enumerated/taxes/septennial.py

Pennsylvania Septennial Census, Freemen List, and Exoneration List models.

Operational Role:
    Specializes TaxAssessmentRecord for SourceRecordCategory.CENSUS_EQUIVALENT
    rolls (e.g., Pennsylvania Septennial Censuses 1779-1863, Freemen Lists,
    and Tax Exoneration Lists).
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.model.source.enumerated.taxes.base import TaxAssessmentRecord

__version__ = "1.0.0+build.2"

__all__ = ["SeptennialCensusRecord"]

_SEPTENNIAL_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.SEPTENNIAL_CENSUS,
        SourceRecordType.FREEMEN_LIST,
        SourceRecordType.EXONERATION_LIST,
    }
)


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class SeptennialCensusRecord(TaxAssessmentRecord):
    """Evidentiary composite for Septennial Censuses and Census-Equivalent Tax Lists."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.CENSUS_EQUIVALENT,
        description="Fixed CENSUS_EQUIVALENT source category.",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.SEPTENNIAL_CENSUS,
        description="Granular census-equivalent roll type.",
    )
    deaf_dumb_or_blind_note: str | None = Field(
        default=None,
        description="Special statutory column notes recorded on Septennial Census returns.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = frozenset(
        {SourceRecordCategory.CENSUS_EQUIVALENT}
    )
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _SEPTENNIAL_TYPES
