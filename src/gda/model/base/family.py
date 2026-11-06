"""Path: src/gda/model/base/family.py

Relational value objects representing domestic unions and pedigree linkages.

Operational Role:
    Defines foundational domestic relational composites ChildLink and FamilyUnion.
    ChildLink encapsulates an associative child IndividualID bounded by lineage
    pedigree classification with total ordering and copy-on-write mutators.
    FamilyUnion encapsulates union inception, dissolution, and temporal bounds
    with factory constructors, copy-on-write mutators, and serialization parity.
"""

from __future__ import annotations

import json
from dataclasses import replace
from functools import total_ordering
from typing import Any, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.enums.vital import PedigreeType, UnionDissolutionType, UnionType
from gda.model.atom.date import EventDate
from gda.model.atom.id import IndividualID
from gda.model.base.time_period import TimePeriod

__version__ = "1.0.0+build.4"

__all__ = ["ChildLink", "FamilyUnion"]

_PEDIGREE_MAP: dict[str, PedigreeType] = {
    "BIRTH": PedigreeType.BIRTH,
    "BIOLOGICAL": PedigreeType.BIRTH,
    "ADOPTED": PedigreeType.ADOPTED,
    "STEP": PedigreeType.STEP,
    "FOSTER": PedigreeType.FOSTER,
    "UNKNOWN": PedigreeType.UNKNOWN,
}

_UNION_TYPE_MAP: dict[str, UnionType] = {
    "MARRIED": UnionType.MARRIED,
    "MARRIAGE": UnionType.MARRIED,
    "COMMON_LAW": UnionType.COMMON_LAW,
    "CIVIL_UNION": UnionType.CIVIL_UNION,
    "INFORMAL": UnionType.INFORMAL,
    "UNKNOWN": UnionType.UNKNOWN,
}

_DISSOLUTION_MAP: dict[str, UnionDissolutionType] = {
    "DIVORCE": UnionDissolutionType.DIVORCE,
    "DIVORCED": UnionDissolutionType.DIVORCE,
    "ANNULMENT": UnionDissolutionType.ANNULMENT,
    "ANNULLED": UnionDissolutionType.ANNULMENT,
    "SEPARATION": UnionDissolutionType.SEPARATION,
    "SEPARATED": UnionDissolutionType.SEPARATION,
    "DEATH": UnionDissolutionType.DEATH,
    "DESERTION": UnionDissolutionType.DESERTION,
    "UNKNOWN": UnionDissolutionType.UNKNOWN,
}


def _normalize_pedigree(pedigree: PedigreeType | str) -> PedigreeType:
    """Normalize pedigree inputs from string tokens or enums."""
    if isinstance(pedigree, PedigreeType):
        return pedigree
    token = str(pedigree).strip().upper()
    if token in _PEDIGREE_MAP:
        return _PEDIGREE_MAP[token]
    raise ModelFormatError(f"Cannot normalize '{pedigree}' to a valid PedigreeType.")


def _normalize_union_type(union_type: UnionType | str) -> UnionType:
    """Normalize union type inputs from string tokens or enums."""
    if isinstance(union_type, UnionType):
        return union_type
    token = str(union_type).strip().upper()
    if token in _UNION_TYPE_MAP:
        return _UNION_TYPE_MAP[token]
    raise ModelFormatError(f"Cannot normalize '{union_type}' to a valid UnionType.")


def _normalize_dissolution(
    dissolution_type: UnionDissolutionType | str | None,
) -> UnionDissolutionType | None:
    """Normalize dissolution type inputs from string tokens or enums."""
    if dissolution_type is None:
        return None
    if isinstance(dissolution_type, UnionDissolutionType):
        return dissolution_type
    token = str(dissolution_type).strip().upper()
    if token in _DISSOLUTION_MAP:
        return _DISSOLUTION_MAP[token]
    raise ModelFormatError(
        f"Cannot normalize '{dissolution_type}' to a valid UnionDissolutionType."
    )


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class ChildLink(IntrospectableMixin):
    """Associative child relationship link within a domestic or biological family unit."""

    child_id: IndividualID = Field(..., description="Canonical IndividualID of the child.")
    pedigree: PedigreeType = Field(
        default=PedigreeType.BIRTH,
        description="Lineage classification: Birth, Adopted, Step, Foster, Unknown.",
    )

    @classmethod
    def create(
        cls,
        child_id: IndividualID | str,
        pedigree: PedigreeType | str = PedigreeType.BIRTH,
    ) -> ChildLink:
        """Factory constructor instantiating a validated ChildLink."""
        cid = child_id if isinstance(child_id, IndividualID) else IndividualID(child_id)
        ped = _normalize_pedigree(pedigree)
        return cls(child_id=cid, pedigree=ped)

    def update_pedigree(self, pedigree: PedigreeType | str) -> Self:
        """Return a new immutable copy with updated pedigree classification."""
        ped = _normalize_pedigree(pedigree)
        if ped == self.pedigree:
            return self
        return replace(self, pedigree=ped)

    def to_dict(self) -> dict[str, Any]:
        """Serialize ChildLink to a dictionary."""
        return {
            "child_id": self.child_id.value,
            "pedigree": self.pedigree.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChildLink:
        """Deserialize a dictionary payload into an immutable ChildLink."""
        if not isinstance(data, dict):
            raise ModelFormatError("ChildLink payload must be a dictionary.")
        cid = data.get("child_id")
        if not cid:
            raise ModelFormatError("Missing required field 'child_id' for ChildLink.")
        ped = data.get("pedigree", PedigreeType.BIRTH)
        return cls.create(child_id=str(cid), pedigree=ped)

    def to_json(self) -> str:
        """Serialize ChildLink to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> ChildLink:
        """Deserialize a JSON string directly into a ChildLink instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse ChildLink JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render readable summary of the child linkage."""
        return f"{self.child_id.value} ({self.pedigree.value})"

    def __repr__(self) -> str:
        """Render explicit representation."""
        return f"ChildLink(child_id={self.child_id!r}, pedigree={self.pedigree})"

    def __lt__(self, other: Any) -> bool:
        """Support deterministic sorting by child_id and pedigree."""
        if isinstance(other, ChildLink):
            if self.child_id != other.child_id:
                return self.child_id < other.child_id
            return self.pedigree.value < other.pedigree.value
        return NotImplemented


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class FamilyUnion(IntrospectableMixin):
    """Characterization of union inception, dissolution, and temporal bounds."""

    union_type: UnionType = Field(
        default=UnionType.UNKNOWN,
        description="Classification of union formation (MARRIED, INFORMAL, etc.).",
    )
    dissolution_type: UnionDissolutionType | None = Field(
        default=None,
        description="Classification of termination (DIVORCE, SEPARATION, DEATH, etc.).",
    )
    period: TimePeriod | None = Field(
        default=None,
        description="Chronological bounds of the union (inception to termination).",
    )

    @classmethod
    def create(
        cls,
        union_type: UnionType | str = UnionType.UNKNOWN,
        dissolution_type: UnionDissolutionType | str | None = None,
        period: TimePeriod | None = None,
    ) -> FamilyUnion:
        """Factory constructor instantiating a validated FamilyUnion."""
        u_type = _normalize_union_type(union_type)
        d_type = _normalize_dissolution(dissolution_type)
        return cls(union_type=u_type, dissolution_type=d_type, period=period)

    def update_type(self, union_type: UnionType | str) -> Self:
        """Return a new immutable copy with updated union type."""
        u_type = _normalize_union_type(union_type)
        if u_type == self.union_type:
            return self
        return replace(self, union_type=u_type)

    def update_dissolution(self, dissolution_type: UnionDissolutionType | str | None) -> Self:
        """Return a new immutable copy with updated dissolution type."""
        d_type = _normalize_dissolution(dissolution_type)
        if d_type == self.dissolution_type:
            return self
        return replace(self, dissolution_type=d_type)

    def update_period(self, period: TimePeriod | None) -> Self:
        """Return a new immutable copy with updated chronological period."""
        if period == self.period:
            return self
        return replace(self, period=period)

    def update_marriage_date(self, date: EventDate | str | None) -> Self:
        """Return a new immutable copy updating the start (marriage/union) date."""
        resolved_date = (
            date if (date is None or isinstance(date, EventDate)) else EventDate.create(date)
        )
        end = self.period.end_date if self.period is not None else None
        if resolved_date is None and end is None:
            new_period = None
        else:
            new_period = TimePeriod(start_date=resolved_date, end_date=end)
        return self.update_period(new_period)

    def update_dissolution_date(self, date: EventDate | str | None) -> Self:
        """Return a new immutable copy updating the end (dissolution) date."""
        resolved_date = (
            date if (date is None or isinstance(date, EventDate)) else EventDate.create(date)
        )
        start = self.period.start_date if self.period is not None else None
        if start is None and resolved_date is None:
            new_period = None
        else:
            new_period = TimePeriod(start_date=start, end_date=resolved_date)
        return self.update_period(new_period)

    def to_dict(self) -> dict[str, Any]:
        """Serialize FamilyUnion to a dictionary."""
        data: dict[str, Any] = {"union_type": self.union_type.value}
        if self.dissolution_type is not None:
            data["dissolution_type"] = self.dissolution_type.value
        if self.period is not None:
            start_str = str(self.period.start_date) if self.period.start_date else None
            end_str = str(self.period.end_date) if self.period.end_date else None
            data["period"] = {"start_date": start_str, "end_date": end_str}
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FamilyUnion:
        """Deserialize a dictionary payload into an immutable FamilyUnion."""
        if not isinstance(data, dict):
            raise ModelFormatError("FamilyUnion payload must be a dictionary.")
        u_type = data.get("union_type", UnionType.UNKNOWN)
        d_type = data.get("dissolution_type")

        raw_period = data.get("period")
        period_obj: TimePeriod | None = None
        if isinstance(raw_period, dict):
            s_str = raw_period.get("start_date")
            e_str = raw_period.get("end_date")
            period_obj = TimePeriod(
                start_date=EventDate.create(s_str) if s_str else None,
                end_date=EventDate.create(e_str) if e_str else None,
            )
        elif isinstance(raw_period, TimePeriod):
            period_obj = raw_period

        return cls.create(
            union_type=u_type,
            dissolution_type=d_type,
            period=period_obj,
        )

    def to_json(self) -> str:
        """Serialize FamilyUnion to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> FamilyUnion:
        """Deserialize a JSON string directly into a FamilyUnion instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse FamilyUnion JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render readable summary of the union state."""
        parts = [f"Type: {self.union_type.value}"]
        if self.dissolution_type:
            parts.append(f"Dissolved: {self.dissolution_type.value}")
        if self.period:
            parts.append(f"Period: {self.period}")
        return ", ".join(parts)
