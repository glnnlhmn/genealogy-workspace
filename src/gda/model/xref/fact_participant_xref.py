"""Path: src/gda/model/xref/fact_participant_xref.py

Cross-reference bridge and index model linking evidentiary facts to participating individuals.

Operational Role:
    Defines FactParticipantXRef (frozen Pydantic dataclass) as a derived relational
    index row linking an active FactID assertion to a participating IndividualID,
    capturing AssociatedRole, FactType, primary subject status, optional
    HistoricalYear, and optional LocationID / SiteID geographic anchors.
"""

from __future__ import annotations

import json
from functools import total_ordering
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.core import AssociatedRole, FactType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.id import FactID, IndividualID, LocationID, SiteID
from gda.model.atom.year import HistoricalYear
from gda.model.entity.fact import Fact
from gda.util.enums import coerce_enum

__version__ = "1.0.0+build.4"

__all__ = [
    "FactParticipantXRef",
]


def _parse_role(raw: AssociatedRole | str) -> AssociatedRole:
    """Resolve AssociatedRole by enum instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(AssociatedRole, raw, field_name="role")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid AssociatedRole value: '{raw}'.") from err


def _parse_fact_type(raw: FactType | str) -> FactType:
    """Resolve FactType by enum instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(FactType, raw, field_name="fact_type")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid FactType value: '{raw}'.") from err


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
class FactParticipantXRef(IntrospectableMixin):
    """Immutable derived index row linking a FactID to a participating IndividualID."""

    fact_id: FactID = Field(
        ...,
        description="Canonical FactID ('FID-######') of the evidentiary fact or event.",
    )
    individual_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID ('IND-######') of the participating person.",
    )
    role: AssociatedRole = Field(
        default=AssociatedRole.PRIMARY,
        description="Contextual role of the individual in the fact.",
    )
    fact_type: FactType = Field(
        ...,
        description="Denormalized FactType for rapid timeline and event filtering.",
    )
    is_primary_subject: bool = Field(
        default=True,
        description="True when the individual is the primary subject of the fact.",
    )
    temporal_year: HistoricalYear | None = Field(
        default=None,
        description="Optional validated 4-digit calendar year (1000..2100) for chronological sorting.",
    )
    location_id: LocationID | None = Field(
        default=None,
        description="Optional macro-jurisdictional LocationID ('LOC-######') from the fact.",
    )
    site_id: SiteID | None = Field(
        default=None,
        description="Optional micro-physical venue SiteID ('SID-######') from the fact.",
    )

    @property
    def xref_key(self) -> str:
        """Return dynamic compound index key '<fact_id>::<individual_id>::<role>'."""
        return f"{self.fact_id.value}::{self.individual_id.value}::{self.role.value}"

    @property
    def sort_key(self) -> tuple[str, int, str, str, str]:
        """Return deterministic ordering tuple (individual_id, year, fact_type, fact_id, role)."""
        year_val = int(self.temporal_year) if self.temporal_year is not None else 9999
        return (
            self.individual_id.value,
            year_val,
            self.fact_type.value,
            self.fact_id.value,
            self.role.value,
        )

    @classmethod
    def create(
        cls,
        fact_id: FactID | str,
        individual_id: IndividualID | str,
        fact_type: FactType | str,
        role: AssociatedRole | str = AssociatedRole.PRIMARY,
        is_primary_subject: bool | None = None,
        temporal_year: HistoricalYear | int | None = None,
        location_id: LocationID | str | None = None,
        site_id: SiteID | str | None = None,
    ) -> FactParticipantXRef:
        """Factory constructor instantiating a validated FactParticipantXRef."""
        res_fact = fact_id if isinstance(fact_id, FactID) else FactID(str(fact_id).strip().upper())
        res_ind = (
            individual_id
            if isinstance(individual_id, IndividualID)
            else IndividualID(str(individual_id).strip().upper())
        )
        res_role = _parse_role(role)
        res_ft = _parse_fact_type(fact_type)
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
            fact_id=res_fact,
            individual_id=res_ind,
            role=res_role,
            fact_type=res_ft,
            is_primary_subject=res_primary,
            temporal_year=res_year,
            location_id=res_loc,
            site_id=res_site,
        )

    @classmethod
    def from_fact(
        cls,
        fact: Fact,
        family_spouse_ids: tuple[IndividualID, ...] = (),
    ) -> tuple[FactParticipantXRef, ...]:
        """Derive FactParticipantXRef rows from an active Fact entity.

        For an individual-anchored Fact, emits the primary subject row plus all
        secondary Fact.participants rows. For a family-anchored Fact, emits primary
        rows for any provided family_spouse_ids plus all secondary Fact.participants.
        """
        if not isinstance(fact, Fact):
            raise ModelFormatError("from_fact requires a Fact entity instance.")

        raw_year = fact.year_lower_bound
        year_atom = HistoricalYear(raw_year) if raw_year is not None else None
        rows: list[FactParticipantXRef] = []
        seen_keys: set[tuple[str, str]] = set()

        if isinstance(fact.primary_subject_id, IndividualID):
            rows.append(
                cls(
                    fact_id=fact.id,
                    individual_id=fact.primary_subject_id,
                    role=AssociatedRole.PRIMARY,
                    fact_type=fact.fact_type,
                    is_primary_subject=True,
                    temporal_year=year_atom,
                    location_id=fact.location_id,
                    site_id=fact.site_id,
                )
            )
            seen_keys.add((fact.primary_subject_id.value, AssociatedRole.PRIMARY.value))
        else:
            for spouse_id in family_spouse_ids:
                key = (spouse_id.value, AssociatedRole.PRIMARY.value)
                if key not in seen_keys:
                    rows.append(
                        cls(
                            fact_id=fact.id,
                            individual_id=spouse_id,
                            role=AssociatedRole.PRIMARY,
                            fact_type=fact.fact_type,
                            is_primary_subject=True,
                            temporal_year=year_atom,
                            location_id=fact.location_id,
                            site_id=fact.site_id,
                        )
                    )
                    seen_keys.add(key)

        for part in fact.participants:
            key = (part.individual_id.value, part.role.value)
            if key not in seen_keys:
                rows.append(
                    cls(
                        fact_id=fact.id,
                        individual_id=part.individual_id,
                        role=part.role,
                        fact_type=fact.fact_type,
                        is_primary_subject=False,
                        temporal_year=year_atom,
                        location_id=fact.location_id,
                        site_id=fact.site_id,
                    )
                )
                seen_keys.add(key)

        return tuple(rows)

    def to_dict(self) -> dict[str, Any]:
        """Serialize FactParticipantXRef to a dictionary."""
        data: dict[str, Any] = {
            "fact_id": self.fact_id.value,
            "individual_id": self.individual_id.value,
            "role": self.role.value,
            "fact_type": self.fact_type.value,
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
    def from_dict(cls, data: dict[str, Any]) -> FactParticipantXRef:
        """Deserialize a dictionary payload into a FactParticipantXRef."""
        if not isinstance(data, dict):
            raise ModelFormatError("FactParticipantXRef payload must be a dictionary.")

        fid = data.get("fact_id")
        iid = data.get("individual_id")
        ft = data.get("fact_type")

        if not all((fid, iid, ft)):
            raise ModelFormatError(
                "FactParticipantXRef requires 'fact_id', 'individual_id', and 'fact_type'."
            )

        return cls.create(
            fact_id=str(fid),
            individual_id=str(iid),
            fact_type=str(ft),
            role=data.get("role", AssociatedRole.PRIMARY),
            is_primary_subject=data.get("is_primary_subject"),
            temporal_year=data.get("temporal_year"),
            location_id=data.get("location_id"),
            site_id=data.get("site_id"),
        )

    def to_json(self) -> str:
        """Serialize FactParticipantXRef to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> FactParticipantXRef:
        """Deserialize a JSON string directly into a FactParticipantXRef."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse FactParticipantXRef JSON string: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __lt__(self, other: Any) -> bool:
        """Support deterministic chronological and entity sorting."""
        if isinstance(other, FactParticipantXRef):
            return self.sort_key < other.sort_key
        return NotImplemented

    def __str__(self) -> str:
        return f"FactParticipantXRef [{self.xref_key}] ({self.fact_type.value})"

    def __repr__(self) -> str:
        return (
            f"FactParticipantXRef(fact_id={self.fact_id!r}, "
            f"individual_id={self.individual_id!r}, role={self.role!r}, "
            f"fact_type={self.fact_type!r})"
        )
