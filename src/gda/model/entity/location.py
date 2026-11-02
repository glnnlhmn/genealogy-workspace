"""Path: src/gda/model/entity/location.py

Jurisdictional boundary and administrative entity model.

Operational Role:
    Defines the Location domain entity representing administrative jurisdictions
    (countries, statoids, counties, civil townships, municipalities, unincorporated places).
    Inherits lifecycle management, audit timestamps, soft-deprecation tombstones, and
    copy-on-write embedded Note collections from BaseEntity[LocationID]. Incorporates
    the modernized NameThing value object for canonical and multi-phase historical naming.
    Provides explicit dirty state tracking (_dirty) and dedicated copy-on-write mutators
    for all jurisdictional fields.
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.archival import NoteType
from gda.enums.location import JurisdictionCategory
from gda.enums.vital import HistoricNameType
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.geo import Coordinates
from gda.model.atom.id import LocationID, NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.entity import BaseEntity
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.note import Note
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.35"

__all__ = ["Location"]

_LOCATION_ID_PATTERN: re.Pattern[str] = re.compile(r"^LOC-\d{6}$")
_LOCATION_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:loc:[a-z0-9_:\-]+$")


@dataclass(
    config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True),
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

        if not self.canonical_urn or not self._URN_PATTERN.match(self.canonical_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:loc:<namespace>'"
            )

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Location cannot be superseded by itself.")

        if self.parent_id is not None and self.parent_id == self.id:
            raise ModelFormatError("Location cannot be its own parent.")

        if self.id in self.predecessor_ids:
            raise ModelFormatError(
                "Location cannot reference itself in predecessor_ids."
            )

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
            location_id
            if isinstance(location_id, LocationID)
            else LocationID(location_id)
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
            else JurisdictionCategory(category)
        )

        resolved_parent = (
            parent_id
            if parent_id is None or isinstance(parent_id, LocationID)
            else LocationID(parent_id)
        )

        resolved_preds = (
            [
                pid if isinstance(pid, LocationID) else LocationID(pid)
                for pid in predecessor_ids
            ]
            if predecessor_ids is not None
            else []
        )

        resolved_succs = (
            [
                sid if isinstance(sid, LocationID) else LocationID(sid)
                for sid in successor_ids
            ]
            if successor_ids is not None
            else []
        )

        now_ts = IsoTimestamp.now_utc()
        resolved_audit = (
            audit
            if audit is not None
            else AuditStamp(created_at=now_ts, updated_at=now_ts)
        )
        resolved_tombstone = (
            tombstone if tombstone is not None else Tombstone[LocationID]()
        )
        resolved_notes = list(notes) if notes is not None else []

        kwargs: dict[str, Any] = {
            "id": resolved_id,
            "name": resolved_name,
            "category": resolved_cat,
            "canonical_urn": canonical_urn.strip() if canonical_urn else "",
            "audit": resolved_audit,
            "tombstone": resolved_tombstone,
            "notes": resolved_notes,
            "parent_id": resolved_parent,
            "predecessor_ids": resolved_preds,
            "successor_ids": resolved_succs,
            "is_primary_local_authority": is_primary_local_authority,
            "is_unincorporated": is_unincorporated,
            "period": period,
            "coordinates": coordinates,
            "_dirty": False,
        }

        return cls(**kwargs)

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
        return replace(
            self,
            name=updated_name,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
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
            audit=self.audit.touch(IsoTimestamp.now_utc()),
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
            audit=self.audit.touch(IsoTimestamp.now_utc()),
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
            audit=self.audit.touch(IsoTimestamp.now_utc()),
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
        return replace(
            self,
            name=new_name,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_category(self, category: JurisdictionCategory | str) -> Self:
        """Return a new immutable copy with updated jurisdictional category."""
        res_cat = (
            category
            if isinstance(category, JurisdictionCategory)
            else JurisdictionCategory(category)
        )
        return replace(
            self,
            category=res_cat,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
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
        return replace(
            self,
            parent_id=res_parent,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_urn(self, canonical_urn: str) -> Self:
        """Return a new immutable copy with updated canonical URN."""
        clean_urn = canonical_urn.strip() if canonical_urn else ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{clean_urn}'. "
                "Must match 'urn:gda:loc:<namespace>'"
            )
        return replace(
            self,
            canonical_urn=clean_urn,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_authority(self, is_primary_local_authority: bool) -> Self:
        """Return a new immutable copy with updated primary local record-keeping authority flag."""
        return replace(
            self,
            is_primary_local_authority=is_primary_local_authority,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_unincorporated(self, is_unincorporated: bool) -> Self:
        """Return a new immutable copy with updated municipal incorporation flag."""
        return replace(
            self,
            is_unincorporated=is_unincorporated,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def add_predecessor(self, predecessor_id: LocationID | str) -> Self:
        """Return a new immutable copy with unique predecessor jurisdiction appended."""
        res_id = (
            predecessor_id
            if isinstance(predecessor_id, LocationID)
            else LocationID(predecessor_id)
        )
        if res_id == self.id:
            raise ModelFormatError(
                "Location cannot reference itself in predecessor_ids."
            )
        if res_id in self.predecessor_ids:
            return self
        return replace(
            self,
            predecessor_ids=[*self.predecessor_ids, res_id],
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def remove_predecessor(self, predecessor_id: LocationID | str) -> Self:
        """Return a new immutable copy with predecessor jurisdiction removed."""
        res_id = (
            predecessor_id
            if isinstance(predecessor_id, LocationID)
            else LocationID(predecessor_id)
        )
        filtered = [pid for pid in self.predecessor_ids if pid != res_id]
        if len(filtered) == len(self.predecessor_ids):
            return self
        return replace(
            self,
            predecessor_ids=filtered,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def add_successor(self, successor_id: LocationID | str) -> Self:
        """Return a new immutable copy with unique successor jurisdiction appended."""
        res_id = (
            successor_id
            if isinstance(successor_id, LocationID)
            else LocationID(successor_id)
        )
        if res_id == self.id:
            raise ModelFormatError("Location cannot reference itself in successor_ids.")
        if res_id in self.successor_ids:
            return self
        return replace(
            self,
            successor_ids=[*self.successor_ids, res_id],
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def remove_successor(self, successor_id: LocationID | str) -> Self:
        """Return a new immutable copy with successor jurisdiction removed."""
        res_id = (
            successor_id
            if isinstance(successor_id, LocationID)
            else LocationID(successor_id)
        )
        filtered = [sid for sid in self.successor_ids if sid != res_id]
        if len(filtered) == len(self.successor_ids):
            return self
        return replace(
            self,
            successor_ids=filtered,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_coordinates(self, coordinates: Coordinates | None) -> Self:
        """Return a new immutable copy with updated spatial coordinates."""
        return replace(
            self,
            coordinates=coordinates,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_period(self, period: TimePeriod | None) -> Self:
        """Return a new immutable copy with updated temporal bounds."""
        return replace(
            self,
            period=period,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
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
        target_str = str(note_id)
        found = False
        new_notes: list[Note] = []
        for n in self.notes:
            if str(n.note_id) == target_str:
                found = True
                updated_n = n
                if text is not None:
                    updated_n = updated_n.update_text(text)
                if title is not None:
                    updated_n = updated_n.update_title(title)
                if note_type is not None:
                    updated_n = updated_n.update_type(note_type)
                if tags is not None:
                    updated_n = updated_n.update_tags(tags)
                new_notes.append(updated_n)
            else:
                new_notes.append(n)

        if not found:
            return self
        return replace(
            self,
            notes=new_notes,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def __str__(self) -> str:
        """Render concise human-readable jurisdictional representation."""
        return f"{self.canonical_name} [{self.category.value}] ({self.id.value})"
