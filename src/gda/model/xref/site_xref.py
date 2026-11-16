"""Path: src/gda/model/xref/site_xref.py

Cross-reference bridge and index model linking physical venues (Sites) to entities and sources.

Operational Role:
    Defines SiteXRef (frozen Pydantic dataclass) as a derived relational index
    row linking a SiteID ('SID-######') and its governing LocationID ('LOC-######')
    to a polymorphic target identifier (canonical SmartIDPrefix AtomID subclass
    or SourceID UUIDv4), exposing IDType and SmartIDPrefix classification properties.
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
from gda.model.atom.id import (
    AtomID,
    LocationID,
    SiteID,
    SourceID,
)
from gda.model.xref.location_xref import _ATOM_PREFIX_MAP, _resolve_target_id

__version__ = "1.0.0+build.1"

__all__ = [
    "SiteTargetID",
    "SiteXRef",
]

type SiteTargetID = AtomID | SourceID


@total_ordering
@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class SiteXRef(IntrospectableMixin):
    """Immutable derived index row linking a SiteID and governing LocationID to an AtomID or SourceID."""

    site_id: SiteID = Field(
        ...,
        description="Canonical SiteID ('SID-######') of the physical venue or landmark.",
    )
    location_id: LocationID = Field(
        ...,
        description="Canonical LocationID ('LOC-######') of the governing civil jurisdiction.",
    )
    target_id: AtomID | SourceID = Field(
        ...,
        description="Canonical AtomID ('AAA-######') or SourceID (UUIDv4) associated with the site.",
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

            if self.target_id.value == self.site_id.value:
                raise ModelFormatError(
                    f"SiteXRef site_id ('{self.site_id.value}') cannot reference itself as target_id."
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
        """Return dynamic compound index key '<site_id>::<target_id>'."""
        return f"{self.site_id.value}::{self.target_id.value}"

    @property
    def sort_key(self) -> tuple[str, str, str]:
        """Return deterministic ordering tuple (site_id, location_id, target_id)."""
        return (self.site_id.value, self.location_id.value, self.target_id.value)

    @classmethod
    def create(
        cls,
        site_id: SiteID | str,
        location_id: LocationID | str,
        target_id: SiteTargetID | str,
    ) -> SiteXRef:
        """Factory constructor instantiating a validated SiteXRef."""
        res_site = site_id if isinstance(site_id, SiteID) else SiteID(str(site_id).strip().upper())
        res_loc = (
            location_id
            if isinstance(location_id, LocationID)
            else LocationID(str(location_id).strip().upper())
        )
        res_target = _resolve_target_id(target_id)
        return cls(site_id=res_site, location_id=res_loc, target_id=res_target)

    def to_dict(self) -> dict[str, Any]:
        """Serialize SiteXRef to a dictionary."""
        return {
            "site_id": self.site_id.value,
            "location_id": self.location_id.value,
            "target_id": self.target_id.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SiteXRef:
        """Deserialize a dictionary payload into a SiteXRef."""
        if not isinstance(data, dict):
            raise ModelFormatError("SiteXRef payload must be a dictionary.")

        sid = data.get("site_id")
        lid = data.get("location_id")
        tid = data.get("target_id")

        if not sid or not lid or not tid:
            raise ModelFormatError("SiteXRef requires 'site_id', 'location_id', and 'target_id'.")

        return cls.create(site_id=str(sid), location_id=str(lid), target_id=str(tid))

    def to_json(self) -> str:
        """Serialize SiteXRef to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> SiteXRef:
        """Deserialize a JSON string directly into a SiteXRef."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse SiteXRef JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __lt__(self, other: Any) -> bool:
        """Support deterministic site, location, and target sorting."""
        if isinstance(other, SiteXRef):
            return self.sort_key < other.sort_key
        return NotImplemented

    def __str__(self) -> str:
        label = (
            self.target_prefix.value
            if self.target_prefix is not None
            else self.target_id_type.value
        )
        return f"SiteXRef [{self.xref_key}] ({self.location_id.value} / {label})"

    def __repr__(self) -> str:
        return (
            f"SiteXRef(site_id={self.site_id!r}, "
            f"location_id={self.location_id!r}, target_id={self.target_id!r})"
        )
