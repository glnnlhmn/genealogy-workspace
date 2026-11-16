"""Path: src/gda/model/xref/location_xref.py

Cross-reference bridge and index model linking civil jurisdictions to entities and sources.

Operational Role:
    Defines LocationXRef (frozen Pydantic dataclass) as a derived relational index
    row linking a LocationID ('LOC-######') to a polymorphic target identifier
    (canonical SmartIDPrefix AtomID subclass or SourceID UUIDv4), exposing
    IDType and SmartIDPrefix classification properties.
"""

from __future__ import annotations

import json
from functools import total_ordering
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.core import IDType, SmartIDPrefix
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ATOM_ID_REGEX, UUID_V4_REGEX
from gda.model.atom.id import (
    AtomID,
    DraftRecordID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    NoteID,
    OrganizationID,
    RepositoryID,
    SiteID,
    SourceID,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "LocationTargetID",
    "LocationXRef",
]

type LocationTargetID = AtomID | SourceID

_ATOM_PREFIX_MAP: dict[SmartIDPrefix, type[AtomID]] = {
    SmartIDPrefix.DRF: DraftRecordID,
    SmartIDPrefix.FID: FactID,
    SmartIDPrefix.FAM: FamilyID,
    SmartIDPrefix.IND: IndividualID,
    SmartIDPrefix.LOC: LocationID,
    SmartIDPrefix.NOT: NoteID,
    SmartIDPrefix.ORG: OrganizationID,
    SmartIDPrefix.REP: RepositoryID,
    SmartIDPrefix.SID: SiteID,
}


def _resolve_target_id(raw: LocationTargetID | str) -> LocationTargetID:
    """Resolve a canonical SmartIDPrefix AtomID subclass, SourceID instance, or raw string token."""
    if isinstance(raw, SourceID):
        return raw

    if isinstance(raw, AtomID):
        try:
            prefix_enum = SmartIDPrefix(raw.prefix)
        except ValueError as exc:
            raise ModelFormatError(
                f"Unsupported SmartIDPrefix '{raw.prefix}' in target_id '{raw.value}'."
            ) from exc
        atom_cls = _ATOM_PREFIX_MAP[prefix_enum]
        return raw if type(raw) is atom_cls else atom_cls(raw.value)

    token = str(raw).strip()
    upper_token = token.upper()
    if ATOM_ID_REGEX.match(upper_token):
        raw_prefix = upper_token.split("-", 1)[0]
        try:
            prefix_enum = SmartIDPrefix(raw_prefix)
        except ValueError as exc:
            raise ModelFormatError(
                f"Unsupported SmartIDPrefix '{raw_prefix}' in target_id '{raw}'."
            ) from exc
        return _ATOM_PREFIX_MAP[prefix_enum](upper_token)

    lower_token = token.lower()
    if UUID_V4_REGEX.match(lower_token):
        return SourceID(lower_token)

    raise ModelFormatError(
        f"Invalid LocationXRef target_id: '{raw}'. Must be a canonical SmartIDPrefix AtomID "
        "('AAA-######') or lowercase RFC 4122 UUIDv4 SourceID."
    )


@total_ordering
@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class LocationXRef(IntrospectableMixin):
    """Immutable derived index row linking a LocationID to a canonical AtomID or SourceID."""

    location_id: LocationID = Field(
        ...,
        description="Canonical LocationID ('LOC-######') of the civil jurisdiction.",
    )
    target_id: AtomID | SourceID = Field(
        ...,
        description="Canonical AtomID ('AAA-######') or SourceID (UUIDv4) anchored to the location.",
    )

    def __post_init__(self) -> None:
        """Enforce canonical SmartIDPrefix membership and non-self-reference when target_id is an AtomID."""
        if isinstance(self.target_id, AtomID):
            try:
                prefix_enum = SmartIDPrefix(self.target_id.prefix)
            except ValueError as exc:
                raise ModelFormatError(
                    f"Unsupported SmartIDPrefix '{self.target_id.prefix}' in target_id '{self.target_id.value}'."
                ) from exc
            expected_cls = _ATOM_PREFIX_MAP[prefix_enum]
            if type(self.target_id) is not expected_cls:
                object.__setattr__(self, "target_id", expected_cls(self.target_id.value))

            if self.target_id.value == self.location_id.value:
                raise ModelFormatError(
                    f"LocationXRef location_id ('{self.location_id.value}') cannot reference itself as target_id."
                )

    @property
    def is_source_target(self) -> bool:
        """Return True when target_id is a SourceID rather than an AtomID."""
        return isinstance(self.target_id, SourceID)

    @property
    def target_id_type(self) -> IDType:
        """Return IDType.UUID for SourceID targets or IDType.SMART_ID for AtomID targets."""
        return IDType.UUID if isinstance(self.target_id, SourceID) else IDType.SMART_ID

    @property
    def target_prefix(self) -> SmartIDPrefix | None:
        """Return SmartIDPrefix for AtomID targets or None for UUID SourceID targets."""
        if isinstance(self.target_id, SourceID):
            return None
        return SmartIDPrefix(self.target_id.prefix)

    @property
    def xref_key(self) -> str:
        """Return dynamic compound index key '<location_id>::<target_id>'."""
        return f"{self.location_id.value}::{self.target_id.value}"

    @property
    def sort_key(self) -> tuple[str, str]:
        """Return deterministic ordering tuple (location_id, target_id)."""
        return (self.location_id.value, self.target_id.value)

    @classmethod
    def create(
        cls,
        location_id: LocationID | str,
        target_id: LocationTargetID | str,
    ) -> LocationXRef:
        """Factory constructor instantiating a validated LocationXRef."""
        res_loc = (
            location_id
            if isinstance(location_id, LocationID)
            else LocationID(str(location_id).strip().upper())
        )
        res_target = _resolve_target_id(target_id)
        return cls(location_id=res_loc, target_id=res_target)

    def to_dict(self) -> dict[str, Any]:
        """Serialize LocationXRef to a dictionary."""
        return {
            "location_id": self.location_id.value,
            "target_id": self.target_id.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LocationXRef:
        """Deserialize a dictionary payload into a LocationXRef."""
        if not isinstance(data, dict):
            raise ModelFormatError("LocationXRef payload must be a dictionary.")

        lid = data.get("location_id")
        tid = data.get("target_id")

        if not lid or not tid:
            raise ModelFormatError("LocationXRef requires 'location_id' and 'target_id'.")

        return cls.create(location_id=str(lid), target_id=str(tid))

    def to_json(self) -> str:
        """Serialize LocationXRef to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> LocationXRef:
        """Deserialize a JSON string directly into a LocationXRef."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse LocationXRef JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __lt__(self, other: Any) -> bool:
        """Support deterministic location and target sorting."""
        if isinstance(other, LocationXRef):
            return self.sort_key < other.sort_key
        return NotImplemented

    def __str__(self) -> str:
        label = (
            self.target_prefix.value
            if self.target_prefix is not None
            else self.target_id_type.value
        )
        return f"LocationXRef [{self.xref_key}] ({label})"

    def __repr__(self) -> str:
        return f"LocationXRef(location_id={self.location_id!r}, target_id={self.target_id!r})"
