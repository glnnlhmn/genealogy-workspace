"""Path: src/gda/model/entity/location.py

Jurisdictional boundary and administrative entity model.

Operational Role:
    Defines the Location domain entity representing administrative jurisdictions
    (countries, statoids, counties, civil townships, municipalities, unincorporated places).
    Inherits lifecycle management, audit timestamps, soft-deprecation tombstones, and
    copy-on-write embedded Note collections from BaseEntity[LocationID]. Incorporates
    the NameThing value object for canonical and multi-phase historical naming,
    Coordinates from gda.model.base.geo, explicit dirty state tracking (_dirty),
    and full dictionary/JSON serialization parity.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.dates import utc_now_iso
from gda.core.enums.archival import NoteType
from gda.core.enums.location import JurisdictionCategory
from gda.core.enums.vital import HistoricNameType
from gda.core.errors import ModelFormatError
from gda.core.types import ENTITY_ID_REGEXES, ENTITY_URN_REGEXES
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import TimePeriod
from gda.model.base.entity import BaseEntity
from gda.model.base.geo import Coordinates
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.3"

__all__ = ["Location"]

_LOCATION_ID_PATTERN: re.Pattern[str] = ENTITY_ID_REGEXES["LOC"]
_LOCATION_URN_PATTERN: re.Pattern[str] = ENTITY_URN_REGEXES["LOC"]


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class Location(BaseEntity[LocationID]):
    """Administrative jurisdiction entity representing a civil territory or government body."""

    name: NameThing = Field(
        ...,
        description="Standardized naming value object containing canonical and historic forms.",
    )
    category: JurisdictionCategory = Field(
        ..., description="Standardized administrative classification tier."
    )
    canonical_urn: str = Field(
        ...,
        description="Deterministic unique URN (e.g., 'urn:gda:loc:us:nh:merrimack:bow').",
    )
    parent_id: LocationID | None = Field(
        default=None, description="Direct parent governing jurisdiction."
    )
    predecessor_ids: list[LocationID] = Field(
        default_factory=list,
        description="Prior jurisdictions partitioned or merged into this.",
    )
    successor_ids: list[LocationID] = Field(
        default_factory=list,
        description="Subsequent jurisdictions created from this entity.",
    )
    is_primary_local_authority: bool = Field(
        default=False,
        description="True if this civil level holds primary record-keeping precedence.",
    )
    is_unincorporated: bool = Field(
        default=False,
        description="True if territory lacks formal municipal incorporation.",
    )
    period: TimePeriod | None = Field(
        default=None,
        description="Temporal bounds spanning establishment to dissolution.",
    )
    coordinates: Coordinates | None = Field(
        default=None, description="Centroid or benchmark spatial coordinates."
    )
    _dirty: bool = Field(
        default=False,
        description="True if entity has unpersisted state changes in working memory.",
    )

    _ID_PATTERN: ClassVar[re.Pattern[str]] = _LOCATION_ID_PATTERN
    _URN_PATTERN: ClassVar[re.Pattern[str]] = _LOCATION_URN_PATTERN

    def __post_init__(self) -> None:
        """Enforce domain invariants, relational integrity, and boundary checks."""
        super().__post_init__()

        if not isinstance(self.id, LocationID):
            raise TypeError(
                f"Location 'id' must be an instance of LocationID, got {type(self.id).__name__}."
            )

        raw_id = self.id.value
        if not self._ID_PATTERN.match(raw_id):
            raise ModelFormatError(
                f"Invalid LocationID format: '{raw_id}'. Must match 'LOC-######'."
            )

        clean_urn = self.canonical_urn.strip() if self.canonical_urn else ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:loc:<namespace>'."
            )
        if clean_urn != self.canonical_urn:
            object.__setattr__(self, "canonical_urn", clean_urn)

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Location cannot be superseded by itself.")

        if self.parent_id is not None and self.parent_id == self.id:
            raise ModelFormatError("Location cannot be its own parent.")

        if self.id in self.predecessor_ids:
            raise ModelFormatError("Location cannot reference itself in predecessor_ids.")

        if self.id in self.successor_ids:
            raise ModelFormatError("Location cannot reference itself in successor_ids.")

        if len(self.predecessor_ids) != len(set(self.predecessor_ids)):
            raise ModelFormatError("Duplicate entries found in predecessor_ids.")

        if len(self.successor_ids) != len(set(self.successor_ids)):
            raise ModelFormatError("Duplicate entries found in successor_ids.")

    @property
    def canonical_name(self) -> str:
        """Forward standardized canonical modern string."""
        return self.name.canonical

    @property
    def is_dirty(self) -> bool:
        """Return True if entity has unpersisted in-memory modifications."""
        return self._dirty

    @property
    def aliases(self) -> list[str]:
        """Forward colloquial naming aliases from naming value object."""
        return self.name.aliases

    @property
    def alternate_names(self) -> list[str]:
        """Backward-compatibility accessor returning aliases list."""
        return self.name.aliases

    @property
    def historical_names(self) -> list[HistoricVariant]:
        """Forward date-bounded evolutionary naming phases from naming value object."""
        return self.name.historic

    @property
    def category_rank(self) -> int:
        """Expose administrative tier sorting priority."""
        return self.category.administrative_rank

    @property
    def sort_key(self) -> tuple[int, str]:
        """Deterministic ordering key sorting by hierarchy tier then canonical name."""
        return (self.category_rank, self.name.canonical.lower())

    @classmethod
    def create(
        cls,
        location_id: LocationID | str,
        name: NameThing | str,
        category: JurisdictionCategory | str,
        canonical_urn: str,
        audit: AuditStamp | None = None,
        tombstone: Tombstone[LocationID] | None = None,
        notes: list[Note] | None = None,
        parent_id: LocationID | str | None = None,
        predecessor_ids: list[LocationID | str] | None = None,
        successor_ids: list[LocationID | str] | None = None,
        is_primary_local_authority: bool = False,
        is_unincorporated: bool = False,
        period: TimePeriod | None = None,
        coordinates: Coordinates | None = None,
    ) -> Location:
        """Factory constructor instantiating a validated Location entity."""
        resolved_id = (
            location_id if isinstance(location_id, LocationID) else LocationID(location_id)
        )

        if isinstance(name, NameThing):
            resolved_name = name
        elif isinstance(name, str):
            clean_str = name.strip()
            if not clean_str:
                raise ModelFormatError("Location 'name' cannot be empty or whitespace.")
            resolved_name = NameThing.create(raw=clean_str, canonical=clean_str)
        else:
            raise TypeError(
                f"Location 'name' must be an instance of NameThing or str, got {type(name).__name__}."
            )

        resolved_cat = (
            category
            if isinstance(category, JurisdictionCategory)
            else JurisdictionCategory(category.strip().upper())
        )

        resolved_parent = (
            parent_id
            if parent_id is None or isinstance(parent_id, LocationID)
            else LocationID(parent_id)
        )

        resolved_preds = (
            [pid if isinstance(pid, LocationID) else LocationID(pid) for pid in predecessor_ids]
            if predecessor_ids is not None
            else []
        )

        resolved_succs = (
            [sid if isinstance(sid, LocationID) else LocationID(sid) for sid in successor_ids]
            if successor_ids is not None
            else []
        )

        now_ts = IsoTimestamp(utc_now_iso())
        resolved_audit = (
            audit if audit is not None else AuditStamp(created_at=now_ts, updated_at=now_ts)
        )
        resolved_tombstone = tombstone if tombstone is not None else Tombstone[LocationID]()
        resolved_notes = list(notes) if notes is not None else []

        return cls(
            id=resolved_id,
            name=resolved_name,
            category=resolved_cat,
            canonical_urn=canonical_urn.strip() if canonical_urn else "",
            audit=resolved_audit,
            tombstone=resolved_tombstone,
            notes=resolved_notes,
            parent_id=resolved_parent,
            predecessor_ids=resolved_preds,
            successor_ids=resolved_succs,
            is_primary_local_authority=is_primary_local_authority,
            is_unincorporated=is_unincorporated,
            period=period,
            coordinates=coordinates,
            _dirty=False,
        )

    def mark_clean(self) -> Self:
        """Return a new immutable copy marking entity as clean (persisted to storage)."""
        if not self._dirty:
            return self
        return replace(self, _dirty=False)

    def mark_dirty(self) -> Self:
        """Return a new immutable copy marking entity as modified in memory."""
        if self._dirty:
            return self
        return replace(self, _dirty=True)

    def add_alias(self, alias: str) -> Self:
        """Return a new immutable copy with unique alias appended to naming value object."""
        updated_name = self.name.add_alias(alias)
        if updated_name is self.name:
            return self
        return replace(
            self,
            name=updated_name,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def remove_alias(self, alias: str) -> Self:
        """Return a new immutable copy with alias removed from naming value object."""
        updated_name = self.name.remove_alias(alias)
        if updated_name is self.name:
            return self
        return replace(
            self,
            name=updated_name,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def add_historic_variant(
        self,
        raw: str,
        name: str | None = None,
        historic_name_type: HistoricNameType | str = HistoricNameType.HISTORICAL,
        valid_period: TimePeriod | None = None,
        comment: str | None = None,
    ) -> Self:
        """Return a new immutable copy appending a historic naming phase."""
        updated_name = self.name.add_historic_variant(
            raw=raw,
            name=name,
            historic_name_type=historic_name_type,
            valid_period=valid_period,
            comment=comment,
        )
        return replace(
            self,
            name=updated_name,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def remove_historic_variant(self, raw: str) -> Self:
        """Return a new immutable copy removing matching historic naming phase by raw text."""
        updated_name = self.name.remove_historic_variant(raw)
        if updated_name is self.name:
            return self
        return replace(
            self,
            name=updated_name,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_name(self, name: NameThing | str) -> Self:
        """Return a new immutable copy with updated naming value object."""
        if isinstance(name, NameThing):
            new_name = name
        elif isinstance(name, str):
            clean_str = name.strip()
            if not clean_str:
                raise ModelFormatError("Location 'name' cannot be empty or whitespace.")
            new_name = NameThing.create(raw=clean_str, canonical=clean_str)
        else:
            raise TypeError(
                f"Location 'name' must be an instance of NameThing or str, got {type(name).__name__}."
            )
        if new_name == self.name:
            return self
        return replace(
            self,
            name=new_name,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_category(self, category: JurisdictionCategory | str) -> Self:
        """Return a new immutable copy with updated jurisdictional category."""
        res_cat = (
            category
            if isinstance(category, JurisdictionCategory)
            else JurisdictionCategory(category.strip().upper())
        )
        if res_cat == self.category:
            return self
        return replace(
            self,
            category=res_cat,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_parent(self, parent_id: LocationID | str | None) -> Self:
        """Return a new immutable copy with updated parent jurisdiction."""
        res_parent = (
            parent_id
            if parent_id is None or isinstance(parent_id, LocationID)
            else LocationID(parent_id)
        )
        if res_parent == self.id:
            raise ModelFormatError("Location cannot be its own parent.")
        if res_parent == self.parent_id:
            return self
        return replace(
            self,
            parent_id=res_parent,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_urn(self, canonical_urn: str) -> Self:
        """Return a new immutable copy with updated canonical URN."""
        clean_urn = canonical_urn.strip() if canonical_urn else ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{clean_urn}'. Must match 'urn:gda:loc:<namespace>'."
            )
        if clean_urn == self.canonical_urn:
            return self
        return replace(
            self,
            canonical_urn=clean_urn,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_authority(self, is_primary_local_authority: bool) -> Self:
        """Return a new immutable copy with updated primary local record-keeping authority flag."""
        if is_primary_local_authority == self.is_primary_local_authority:
            return self
        return replace(
            self,
            is_primary_local_authority=is_primary_local_authority,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_unincorporated(self, is_unincorporated: bool) -> Self:
        """Return a new immutable copy with updated municipal incorporation flag."""
        if is_unincorporated == self.is_unincorporated:
            return self
        return replace(
            self,
            is_unincorporated=is_unincorporated,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def add_predecessor(self, predecessor_id: LocationID | str) -> Self:
        """Return a new immutable copy with unique predecessor jurisdiction appended."""
        res_id = (
            predecessor_id if isinstance(predecessor_id, LocationID) else LocationID(predecessor_id)
        )
        if res_id == self.id:
            raise ModelFormatError("Location cannot reference itself in predecessor_ids.")
        if res_id in self.predecessor_ids:
            return self
        return replace(
            self,
            predecessor_ids=[*self.predecessor_ids, res_id],
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def remove_predecessor(self, predecessor_id: LocationID | str) -> Self:
        """Return a new immutable copy with predecessor jurisdiction removed."""
        res_id = (
            predecessor_id if isinstance(predecessor_id, LocationID) else LocationID(predecessor_id)
        )
        filtered = [pid for pid in self.predecessor_ids if pid != res_id]
        if len(filtered) == len(self.predecessor_ids):
            return self
        return replace(
            self,
            predecessor_ids=filtered,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def add_successor(self, successor_id: LocationID | str) -> Self:
        """Return a new immutable copy with unique successor jurisdiction appended."""
        res_id = successor_id if isinstance(successor_id, LocationID) else LocationID(successor_id)
        if res_id == self.id:
            raise ModelFormatError("Location cannot reference itself in successor_ids.")
        if res_id in self.successor_ids:
            return self
        return replace(
            self,
            successor_ids=[*self.successor_ids, res_id],
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def remove_successor(self, successor_id: LocationID | str) -> Self:
        """Return a new immutable copy with successor jurisdiction removed."""
        res_id = successor_id if isinstance(successor_id, LocationID) else LocationID(successor_id)
        filtered = [sid for sid in self.successor_ids if sid != res_id]
        if len(filtered) == len(self.successor_ids):
            return self
        return replace(
            self,
            successor_ids=filtered,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_coordinates(self, coordinates: Coordinates | None) -> Self:
        """Return a new immutable copy with updated spatial coordinates."""
        if coordinates == self.coordinates:
            return self
        return replace(
            self,
            coordinates=coordinates,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_period(self, period: TimePeriod | None) -> Self:
        """Return a new immutable copy with updated temporal bounds."""
        if period == self.period:
            return self
        return replace(
            self,
            period=period,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_note(
        self,
        note_id: NoteID | str,
        text: str | None = None,
        title: str | None = None,
        note_type: NoteType | str | None = None,
        tags: list[str] | None = None,
    ) -> Self:
        """Return a new immutable copy with the targeted embedded note updated."""
        updated = super().update_note(
            note_id=note_id,
            text=text,
            title=title,
            note_type=note_type,
            tags=tags,
        )
        if updated is self:
            return self
        return replace(updated, _dirty=True)

    def to_dict(self) -> dict[str, Any]:
        """Serialize Location entity to a dictionary payload."""
        data: dict[str, Any] = {
            "id": self.id.value,
            "name": self.name.to_dict(),
            "category": self.category.value,
            "canonical_urn": self.canonical_urn,
            "predecessor_ids": [pid.value for pid in self.predecessor_ids],
            "successor_ids": [sid.value for sid in self.successor_ids],
            "is_primary_local_authority": self.is_primary_local_authority,
            "is_unincorporated": self.is_unincorporated,
            "audit": {
                "created_at": str(self.audit.created_at),
                "updated_at": str(self.audit.updated_at),
            },
            "tombstone": {
                "is_deprecated": self.tombstone.is_deprecated,
                "deprecated_at": (
                    str(self.tombstone.deprecated_at)
                    if self.tombstone.deprecated_at is not None
                    else None
                ),
                "superseded_by": (
                    str(self.tombstone.superseded_by)
                    if self.tombstone.superseded_by is not None
                    else None
                ),
            },
            "notes": [n.to_dict() for n in self.notes],
        }
        if self.parent_id is not None:
            data["parent_id"] = self.parent_id.value
        if self.period is not None:
            data["period"] = self.period.to_dict()
        if self.coordinates is not None:
            data["coordinates"] = self.coordinates.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Location:
        """Deserialize a dictionary payload into an immutable Location entity."""
        if not isinstance(data, dict):
            raise ModelFormatError("Location payload must be a dictionary.")

        raw_id = data.get("id")
        if not raw_id:
            raise ModelFormatError("Missing required field 'id' for Location.")

        raw_name = data.get("name")
        if not raw_name:
            raise ModelFormatError("Missing required field 'name' for Location.")

        raw_category = data.get("category")
        if not raw_category:
            raise ModelFormatError("Missing required field 'category' for Location.")

        resolved_name: NameThing | str = (
            NameThing.from_dict(raw_name) if isinstance(raw_name, dict) else raw_name
        )

        raw_period = data.get("period")
        resolved_period: TimePeriod | None = None
        if isinstance(raw_period, TimePeriod):
            resolved_period = raw_period
        elif isinstance(raw_period, dict) and (
            raw_period.get("start_date") is not None or raw_period.get("end_date") is not None
        ):
            resolved_period = TimePeriod.from_dict(raw_period)

        raw_coords = data.get("coordinates")
        resolved_coords: Coordinates | None = None
        if isinstance(raw_coords, Coordinates):
            resolved_coords = raw_coords
        elif isinstance(raw_coords, dict):
            resolved_coords = Coordinates.from_dict(raw_coords)

        audit_payload = data.get("audit")
        audit_obj: AuditStamp | None = None
        if isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )

        tombstone_payload = data.get("tombstone")
        tombstone_obj: Tombstone[LocationID] | None = None
        if isinstance(tombstone_payload, dict):
            tombstone_obj = Tombstone[LocationID](
                is_deprecated=tombstone_payload.get("is_deprecated", False),
                deprecated_at=(
                    IsoTimestamp(tombstone_payload["deprecated_at"])
                    if tombstone_payload.get("deprecated_at")
                    else None
                ),
                superseded_by=(
                    LocationID(tombstone_payload["superseded_by"])
                    if tombstone_payload.get("superseded_by")
                    else None
                ),
            )

        notes_payload = data.get("notes", [])
        notes_list = [Note.from_dict(n) for n in notes_payload if isinstance(n, dict)]

        return cls.create(
            location_id=str(raw_id),
            name=resolved_name,
            category=str(raw_category),
            canonical_urn=str(data.get("canonical_urn", "")),
            audit=audit_obj,
            tombstone=tombstone_obj,
            notes=notes_list,
            parent_id=data.get("parent_id"),
            predecessor_ids=data.get("predecessor_ids"),
            successor_ids=data.get("successor_ids"),
            is_primary_local_authority=bool(data.get("is_primary_local_authority", False)),
            is_unincorporated=bool(data.get("is_unincorporated", False)),
            period=resolved_period,
            coordinates=resolved_coords,
        )

    def to_json(self) -> str:
        """Serialize Location entity to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Location:
        """Deserialize a JSON string directly into a Location instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse Location JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render concise human-readable jurisdictional representation."""
        return f"{self.canonical_name} [{self.category.value}] ({self.id.value})"

    def __repr__(self) -> str:
        return (
            f"Location(id={self.id!r}, canonical_name={self.canonical_name!r}, "
            f"category={self.category!r}, canonical_urn={self.canonical_urn!r})"
        )
