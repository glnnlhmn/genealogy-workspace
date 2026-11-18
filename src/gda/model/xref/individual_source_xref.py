"""Path: src/gda/model/xref/individual_source_xref.py

Cross-reference bridge and index model linking archival sources to individuals.

Operational Role:
    Defines IndividualSourceXRef (frozen Pydantic dataclass) as a derived relational
    index row linking a SourceID to a participating IndividualID, capturing
    AssociatedRole, SourceRecordCategory, SourceRecordType, primary subject status,
    optional HistoricalYear, and optional LocationID / SiteID geographic anchors.
"""

from __future__ import annotations

import json
from functools import total_ordering
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.core import AssociatedRole
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.id import IndividualID, LocationID, SiteID, SourceID
from gda.model.atom.year import HistoricalYear
from gda.util.enums import coerce_enum

__version__ = "1.0.0+build.2"

__all__ = [
    "IndividualSourceXRef",
]


def _parse_role(raw: AssociatedRole | str) -> AssociatedRole:
    """Resolve AssociatedRole by enum instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(AssociatedRole, raw, field_name="role")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid AssociatedRole value: '{raw}'.") from err


def _parse_record_category(raw: SourceRecordCategory | str) -> SourceRecordCategory:
    """Resolve SourceRecordCategory by enum instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(SourceRecordCategory, raw, field_name="record_category")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid SourceRecordCategory value: '{raw}'.") from err


def _parse_record_type(raw: SourceRecordType | str) -> SourceRecordType:
    """Resolve SourceRecordType by enum instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(SourceRecordType, raw, field_name="record_type")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid SourceRecordType value: '{raw}'.") from err


def _resolve_temporal_year(raw: HistoricalYear | int | None) -> HistoricalYear | None:
    """Resolve HistoricalYear instance, strict integer year, or None."""
    if raw is None or isinstance(raw, HistoricalYear):
        return raw
    return HistoricalYear(raw)


@total_ordering
@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class IndividualSourceXRef(IntrospectableMixin):
    """Immutable derived index row linking a SourceID to a participating IndividualID."""

    source_id: SourceID = Field(
        ...,
        description="Canonical SourceID (UUIDv4) of the archival source document.",
    )
    individual_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID ('IND-######') of the person mentioned in the source.",
    )
    role: AssociatedRole = Field(
        default=AssociatedRole.PRIMARY,
        description="Contextual role of the individual in the source document.",
    )
    record_category: SourceRecordCategory = Field(
        ...,
        description="High-level archival domain category (VITAL, CENSUS, PROBATE, LAND, etc.).",
    )
    record_type: SourceRecordType = Field(
        ...,
        description="Granular archival document classification (BIRTH_CERTIFICATE, DEED_INDENTURE, etc.).",
    )
    is_primary_subject: bool = Field(
        default=True,
        description="True when the individual is a primary subject of the source record.",
    )
    temporal_year: HistoricalYear | None = Field(
        default=None,
        description="Optional validated 4-digit calendar year (1000..2100) for chronological sorting.",
    )
    location_id: LocationID | None = Field(
        default=None,
        description="Optional macro-jurisdictional LocationID ('LOC-######') associated with the source.",
    )
    site_id: SiteID | None = Field(
        default=None,
        description="Optional micro-physical venue SiteID ('SID-######') associated with the source.",
    )

    @property
    def xref_key(self) -> str:
        """Return dynamic compound index key '<source_id>::<individual_id>::<role>'."""
        return f"{self.source_id.value}::{self.individual_id.value}::{self.role.value}"

    @property
    def sort_key(self) -> tuple[str, int, str, str, str, str]:
        """Return deterministic ordering tuple (individual_id, year, category, type, source_id, role)."""
        year_val = int(self.temporal_year) if self.temporal_year is not None else 9999
        return (
            self.individual_id.value,
            year_val,
            self.record_category.value,
            self.record_type.value,
            self.source_id.value,
            self.role.value,
        )

    @classmethod
    def create(
        cls,
        source_id: SourceID | str,
        individual_id: IndividualID | str,
        record_category: SourceRecordCategory | str,
        record_type: SourceRecordType | str,
        role: AssociatedRole | str = AssociatedRole.PRIMARY,
        is_primary_subject: bool | None = None,
        temporal_year: HistoricalYear | int | None = None,
        location_id: LocationID | str | None = None,
        site_id: SiteID | str | None = None,
    ) -> IndividualSourceXRef:
        """Factory constructor instantiating a validated IndividualSourceXRef."""
        res_src = (
            source_id
            if isinstance(source_id, SourceID)
            else SourceID(str(source_id).strip().lower())
        )
        res_ind = (
            individual_id
            if isinstance(individual_id, IndividualID)
            else IndividualID(str(individual_id).strip().upper())
        )
        res_role = _parse_role(role)
        res_cat = _parse_record_category(record_category)
        res_type = _parse_record_type(record_type)
        res_primary = (
            is_primary_subject
            if is_primary_subject is not None
            else (res_role is AssociatedRole.PRIMARY)
        )
        res_year = _resolve_temporal_year(temporal_year)
        res_loc = (
            location_id
            if (location_id is None or isinstance(location_id, LocationID))
            else LocationID(str(location_id).strip().upper())
        )
        res_site = (
            site_id
            if (site_id is None or isinstance(site_id, SiteID))
            else SiteID(str(site_id).strip().upper())
        )

        return cls(
            source_id=res_src,
            individual_id=res_ind,
            role=res_role,
            record_category=res_cat,
            record_type=res_type,
            is_primary_subject=res_primary,
            temporal_year=res_year,
            location_id=res_loc,
            site_id=res_site,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize IndividualSourceXRef to a dictionary."""
        data: dict[str, Any] = {
            "source_id": self.source_id.value,
            "individual_id": self.individual_id.value,
            "role": self.role.value,
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "is_primary_subject": self.is_primary_subject,
        }
        if self.temporal_year is not None:
            data["temporal_year"] = int(self.temporal_year)
        if self.location_id is not None:
            data["location_id"] = self.location_id.value
        if self.site_id is not None:
            data["site_id"] = self.site_id.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndividualSourceXRef:
        """Deserialize a dictionary payload into an IndividualSourceXRef."""
        if not isinstance(data, dict):
            raise ModelFormatError("IndividualSourceXRef payload must be a dictionary.")

        sid = data.get("source_id")
        iid = data.get("individual_id")
        rcat = data.get("record_category")
        rtype = data.get("record_type")

        if not all((sid, iid, rcat, rtype)):
            raise ModelFormatError(
                "IndividualSourceXRef requires 'source_id', 'individual_id', "
                "'record_category', and 'record_type'."
            )

        return cls.create(
            source_id=str(sid),
            individual_id=str(iid),
            record_category=str(rcat),
            record_type=str(rtype),
            role=data.get("role", AssociatedRole.PRIMARY),
            is_primary_subject=data.get("is_primary_subject"),
            temporal_year=data.get("temporal_year"),
            location_id=data.get("location_id"),
            site_id=data.get("site_id"),
        )

    def to_json(self) -> str:
        """Serialize IndividualSourceXRef to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> IndividualSourceXRef:
        """Deserialize a JSON string directly into an IndividualSourceXRef."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse IndividualSourceXRef JSON string: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __lt__(self, other: Any) -> bool:
        """Support deterministic chronological and category sorting."""
        if isinstance(other, IndividualSourceXRef):
            return self.sort_key < other.sort_key
        return NotImplemented

    def __str__(self) -> str:
        return (
            f"IndividualSourceXRef [{self.xref_key}] "
            f"({self.record_category.value}/{self.record_type.value})"
        )

    def __repr__(self) -> str:
        return (
            f"IndividualSourceXRef(source_id={self.source_id!r}, "
            f"individual_id={self.individual_id!r}, role={self.role!r}, "
            f"record_category={self.record_category!r}, record_type={self.record_type!r})"
        )
