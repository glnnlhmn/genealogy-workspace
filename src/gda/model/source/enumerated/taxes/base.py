"""Path: src/gda/model/source/enumerated/taxes/base.py

Historical tax assessment and fiscal valuation roll domain models.

Operational Role:
    Models county, town, and parish tax lists (real estate, personal property,
    poll, and occupation taxes) aligned with tax_assessment.schema.json,
    including dictionary/JSON round-trip serialization.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.constants import TAX_ASSESSMENT_MIN_YEAR
from gda.core.enums.fiscal import TaxpayerClassification
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.id import IndividualID
from gda.model.source.enumerated.base import (
    EnumeratedRollRecord,
    coerce_field_value,
    serialize_primitive_value,
)

__version__ = "1.0.0+build.3"

__all__ = [
    "AssessedProperty",
    "TaxAssessmentRecord",
    "TaxpayerClassification",
]

_TAX_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.TAX,
        SourceRecordCategory.FISCAL,
        SourceRecordCategory.CENSUS_EQUIVALENT,
    }
)

_TAX_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.REAL_ESTATE_TAX,
        SourceRecordType.PERSONAL_PROPERTY_TAX,
        SourceRecordType.POLL_TAX,
        SourceRecordType.SEPTENNIAL_CENSUS,
        SourceRecordType.OCCUPATION_TAX,
        SourceRecordType.FREEMEN_LIST,
        SourceRecordType.EXONERATION_LIST,
    }
)


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class AssessedProperty(IntrospectableMixin):
    """Assessed acreage, livestock, industrial improvements, and tax amounts."""

    acres_seated: float | None = Field(
        default=None, ge=0.0, description="Number of seated/improved acres assessed."
    )
    acres_unseated: float | None = Field(
        default=None, ge=0.0, description="Number of unseated/unimproved acres assessed."
    )
    horses: int | None = Field(default=None, ge=0, description="Number of horses assessed.")
    cattle_or_cows: int | None = Field(
        default=None, ge=0, description="Number of cattle, oxen, or cows assessed."
    )
    mills_distilleries_taverns: str | None = Field(
        default=None,
        description="Verbatim notation of gristmills, sawmills, stills, ferries, or taverns.",
    )
    total_valuation_raw: str | None = Field(
        default=None,
        description="Verbatim assessed valuation (pounds/shillings/pence or USD).",
    )
    county_tax_amount_raw: str | None = Field(
        default=None, description="Verbatim county tax levy assessed."
    )
    state_tax_amount_raw: str | None = Field(
        default=None, description="Verbatim state or provincial tax levy assessed."
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize AssessedProperty fields to a dictionary."""
        return {
            f.name: serialize_primitive_value(getattr(self, f.name))
            for f in dataclasses.fields(self)
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize a dictionary payload into an immutable AssessedProperty."""
        if not isinstance(data, dict):
            raise ModelFormatError("AssessedProperty payload must be a dictionary.")
        return cls(
            **{k: v for k, v in data.items() if k in {f.name for f in dataclasses.fields(cls)}}
        )

    def to_json(self) -> str:
        """Serialize AssessedProperty to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        """Deserialize a JSON string directly into an AssessedProperty."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse AssessedProperty JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(acres_seated={self.acres_seated!r}, "
            f"acres_unseated={self.acres_unseated!r}, total_valuation_raw={self.total_valuation_raw!r})"
        )


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class TaxAssessmentRecord(EnumeratedRollRecord):
    """Evidentiary composite for historical tax assessment and fiscal roll entries."""

    record_type: SourceRecordType = Field(
        default=SourceRecordType.REAL_ESTATE_TAX,
        description="Granular tax or fiscal list classification.",
    )
    roll_locator_raw: str = Field(
        ...,
        description="Verbatim page, folio, or list locator within the tax book.",
    )
    schedule_name: str | None = Field(
        default=None,
        description="Named tax schedule or rate list heading (e.g., 'Seated Land', 'Single Freemen').",
    )
    line_number: int | None = Field(
        default=None,
        ge=1,
        description="Line number on the tax roll if numbered.",
    )
    taxpayer_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the assessed taxpayer.",
    )
    taxpayer_name_raw: str = Field(
        ...,
        description="Verbatim transcribed name of the taxpayer on the roll.",
    )
    classification: TaxpayerClassification | None = Field(
        default=None,
        description="Historical tax status classification (Freeholder, Tenant, Single Freeman, etc.).",
    )
    stated_occupation: str | None = Field(
        default=None,
        description="Trade, calling, or occupation recorded on the tax list.",
    )
    assessed_property: AssessedProperty | None = Field(
        default=None,
        description="Structured valuation, acreage, livestock, and tax levy details.",
    )
    tax_note: str | None = Field(
        default=None,
        description="Archival note on abatement, delinquency, transfer, or non-residency.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _TAX_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _TAX_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce tax category/type, year floor, and taxpayer string hygiene."""
        super().__post_init__()

        if self.record_category not in self.ALLOWED_CATEGORIES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_category in "
                f"{sorted(c.value for c in self.ALLOWED_CATEGORIES)}, got '{self.record_category.value}'."
            )

        if self.record_type not in self.ALLOWED_RECORD_TYPES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_type in "
                f"{sorted(t.value for t in self.ALLOWED_RECORD_TYPES)}, got '{self.record_type.value}'."
            )

        if self.enumeration_year.value < TAX_ASSESSMENT_MIN_YEAR:
            raise ModelFormatError(
                f"{self.__class__.__name__} enumeration_year must be {TAX_ASSESSMENT_MIN_YEAR} or later, "
                f"got {self.enumeration_year.value}."
            )

        loc_clean = self.roll_locator_raw.strip()
        if not loc_clean:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'roll_locator_raw' cannot be empty or whitespace."
            )
        if loc_clean != self.roll_locator_raw:
            object.__setattr__(self, "roll_locator_raw", loc_clean)

        tp_clean = self.taxpayer_name_raw.strip()
        if not tp_clean:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'taxpayer_name_raw' cannot be empty or whitespace."
            )
        if tp_clean != self.taxpayer_name_raw:
            object.__setattr__(self, "taxpayer_name_raw", tp_clean)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize a dictionary payload into an immutable TaxAssessmentRecord subclass."""
        kwargs = cls._parse_base_source_kwargs(data)
        base_keys = set(kwargs.keys())

        for f in dataclasses.fields(cls):
            if f.name in base_keys or f.name not in data:
                continue
            if f.name == "assessed_property" and data["assessed_property"] is not None:
                raw_prop = data["assessed_property"]
                kwargs["assessed_property"] = (
                    raw_prop
                    if isinstance(raw_prop, AssessedProperty)
                    else AssessedProperty.from_dict(raw_prop)
                )
            else:
                kwargs[f.name] = coerce_field_value(str(f.type), data[f.name])

        return cls(**kwargs)
