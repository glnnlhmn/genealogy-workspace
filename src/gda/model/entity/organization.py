"""Path: src/gda/model/entity/organization.py

Voluntary association, fraternal society, religious body, and civic organization entity model.

Operational Role:
    Defines Organization representing human associations and institutions that
    individuals join or affiliate with (e.g., fraternal lodges, church congregations,
    men's choirs, labor guilds, veterans' posts, and civic societies). Inherits
    lifecycle management, audit timestamps, soft-deprecation tombstones, and embedded
    Note collections from BaseEntity[OrganizationID]. Incorporates NameThing for
    temporal naming evolution, OrganizationCategory, optional parent_org_id (and
    parent_id alias) for chapter-to-grand-body hierarchies, predecessor_ids and
    successor_ids for institutional lineage/mergers, optional LocationID and
    meeting SiteID references, TimePeriod bounds, explicit in-memory dirty tracking
    (_dirty), and full dictionary/JSON serialization parity.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import replace
from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.dates import utc_now_iso
from gda.core.enums.archival import NoteType
from gda.core.enums.orgs import OrganizationCategory
from gda.core.enums.vital import HistoricNameType
from gda.core.errors import ModelFormatError
from gda.core.types import ENTITY_ID_REGEXES, ENTITY_URN_REGEXES
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, NoteID, OrganizationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.entity import BaseEntity
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.3"

__all__ = [
    "Organization",
    "OrganizationEntityModel",
]

_ORG_ID_PATTERN: re.Pattern[str] = ENTITY_ID_REGEXES["ORG"]
_ORG_URN_PATTERN: re.Pattern[str] = ENTITY_URN_REGEXES["ORG"]


def _resolve_org_name(name: NameThing | str) -> NameThing:
    """Resolve NameThing instance or non-blank string into NameThing."""
    if isinstance(name, NameThing):
        return name
    if isinstance(name, str):
        clean_str = name.strip()
        if not clean_str:
            raise ModelFormatError("Organization 'name' cannot be empty or whitespace.")
        return NameThing.create(raw=clean_str, canonical=clean_str)
    raise TypeError(
        f"Organization 'name' must be an instance of NameThing or str, got {type(name).__name__}."
    )


def _resolve_org_category(category: OrganizationCategory | str) -> OrganizationCategory:
    """Resolve OrganizationCategory enum or string token."""
    if isinstance(category, OrganizationCategory):
        return category
    if isinstance(category, str):
        try:
            return OrganizationCategory(category.strip().upper())
        except ValueError as exc:
            raise ModelFormatError(f"Invalid OrganizationCategory value: '{category}'.") from exc
    raise TypeError(
        f"Organization 'category' must be OrganizationCategory or str, "
        f"got {type(category).__name__}."
    )


def _resolve_org_id_list(
    items: Sequence[OrganizationID | str] | None,
) -> list[OrganizationID]:
    """Coerce an optional sequence of OrganizationID or string tokens into a list of OrganizationID."""
    if items is None:
        return []
    return [item if isinstance(item, OrganizationID) else OrganizationID(item) for item in items]


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class Organization(BaseEntity[OrganizationID]):
    """Primary voluntary association, society, congregation, or institutional entity model."""

    name: NameThing = Field(
        ...,
        description="Standardized naming value object containing canonical and historic forms.",
    )
    category: OrganizationCategory = Field(
        ...,
        description="Controlled functional classification of the organization.",
    )
    canonical_urn: str = Field(
        ...,
        description="Semantic deterministic lookup URN (e.g., 'urn:gda:org:us:nh:concord:vfw_post_411').",
    )
    parent_org_id: OrganizationID | None = Field(
        default=None,
        description="Optional parent organization reference (e.g., Grand Lodge or national body).",
    )
    predecessor_ids: list[OrganizationID] = Field(
        default_factory=list,
        description="Prior organizations merged, split, or re-chartered into this entity.",
    )
    successor_ids: list[OrganizationID] = Field(
        default_factory=list,
        description="Subsequent organizations created or consolidated from this entity.",
    )
    location_id: LocationID | None = Field(
        default=None,
        description="Optional civil jurisdiction where the organization or chapter operates.",
    )
    meeting_site_id: SiteID | None = Field(
        default=None,
        description="Optional physical Site reference where the organization meets or worships.",
    )
    period: TimePeriod | None = Field(
        default=None,
        description="Structured temporal bounds spanning charter/founding to dissolution.",
    )
    is_active: bool = Field(
        default=True,
        description="Indicates whether the organization is currently active or extant.",
    )
    _dirty: bool = Field(
        default=False,
        description="True if entity has unpersisted state changes in working memory.",
    )

    _ID_PATTERN: ClassVar[re.Pattern[str]] = _ORG_ID_PATTERN
    _URN_PATTERN: ClassVar[re.Pattern[str]] = _ORG_URN_PATTERN

    def __post_init__(self) -> None:
        """Enforce domain invariants, institutional hierarchy integrity, and boundary guards."""
        super().__post_init__()

        if not isinstance(self.id, OrganizationID):
            raise TypeError(
                f"Organization 'id' must be an instance of OrganizationID, "
                f"got {type(self.id).__name__}."
            )

        raw_id = self.id.value
        if not self._ID_PATTERN.match(raw_id):
            raise ModelFormatError(
                f"Invalid OrganizationID format: '{raw_id}'. Must match 'ORG-######'."
            )

        clean_urn = self.canonical_urn.strip() if self.canonical_urn else ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:org:<namespace>'."
            )
        if clean_urn != self.canonical_urn:
            object.__setattr__(self, "canonical_urn", clean_urn)

        if self.parent_org_id is not None and self.parent_org_id.value == raw_id:
            raise ModelFormatError("Organization cannot be its own parent_org_id.")

        if self.id in self.predecessor_ids:
            raise ModelFormatError("Organization cannot reference itself in predecessor_ids.")

        if self.id in self.successor_ids:
            raise ModelFormatError("Organization cannot reference itself in successor_ids.")

        if len(self.predecessor_ids) != len(set(self.predecessor_ids)):
            raise ModelFormatError("Duplicate entries found in predecessor_ids.")

        if len(self.successor_ids) != len(set(self.successor_ids)):
            raise ModelFormatError("Duplicate entries found in successor_ids.")

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Organization cannot be superseded by itself.")

    @property
    def canonical_name(self) -> str:
        """Forward standardized canonical modern string."""
        return self.name.canonical

    @property
    def parent_id(self) -> OrganizationID | None:
        """Return parent_org_id for structural parity with Location.parent_id."""
        return self.parent_org_id

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
        """Forward aliases list for parity with Location and Site."""
        return self.name.aliases

    @property
    def historical_names(self) -> list[HistoricVariant]:
        """Forward date-bounded evolutionary naming phases from naming value object."""
        return self.name.historic

    @property
    def date_founded(self) -> EventDate | None:
        """Convenience accessor for organization founding/charter date from period."""
        return self.period.start_date if self.period is not None else None

    @property
    def date_dissolved(self) -> EventDate | None:
        """Convenience accessor for organization dissolution date from period."""
        return self.period.end_date if self.period is not None else None

    @classmethod
    def create(
        cls,
        org_id: OrganizationID | str,
        name: NameThing | str,
        category: OrganizationCategory | str,
        canonical_urn: str,
        parent_org_id: OrganizationID | str | None = None,
        predecessor_ids: Sequence[OrganizationID | str] | None = None,
        successor_ids: Sequence[OrganizationID | str] | None = None,
        location_id: LocationID | str | None = None,
        meeting_site_id: SiteID | str | None = None,
        audit: AuditStamp | None = None,
        tombstone: Tombstone[OrganizationID] | None = None,
        notes: Sequence[Note] | None = None,
        period: TimePeriod | None = None,
        is_active: bool = True,
    ) -> Organization:
        """Factory constructor instantiating a validated Organization entity."""
        resolved_id = org_id if isinstance(org_id, OrganizationID) else OrganizationID(org_id)
        resolved_name = _resolve_org_name(name)
        resolved_cat = _resolve_org_category(category)

        resolved_parent = (
            parent_org_id
            if (parent_org_id is None or isinstance(parent_org_id, OrganizationID))
            else OrganizationID(parent_org_id)
        )
        resolved_loc = (
            location_id
            if (location_id is None or isinstance(location_id, LocationID))
            else LocationID(location_id)
        )
        resolved_site = (
            meeting_site_id
            if (meeting_site_id is None or isinstance(meeting_site_id, SiteID))
            else SiteID(meeting_site_id)
        )

        resolved_audit = audit if audit is not None else AuditStamp.now()
        resolved_tombstone = tombstone if tombstone is not None else Tombstone[OrganizationID]()
        resolved_notes = list(notes) if notes is not None else []

        return cls(
            id=resolved_id,
            name=resolved_name,
            category=resolved_cat,
            canonical_urn=canonical_urn.strip() if canonical_urn else "",
            parent_org_id=resolved_parent,
            predecessor_ids=_resolve_org_id_list(predecessor_ids),
            successor_ids=_resolve_org_id_list(successor_ids),
            location_id=resolved_loc,
            meeting_site_id=resolved_site,
            audit=resolved_audit,
            tombstone=resolved_tombstone,
            notes=resolved_notes,
            period=period,
            is_active=is_active,
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
        new_name = _resolve_org_name(name)
        if new_name == self.name:
            return self
        return replace(
            self,
            name=new_name,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_category(self, category: OrganizationCategory | str) -> Self:
        """Return a new immutable copy with updated organization classification."""
        res_cat = _resolve_org_category(category)
        if res_cat == self.category:
            return self
        return replace(
            self,
            category=res_cat,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_parent_org(self, parent_org_id: OrganizationID | str | None) -> Self:
        """Return a new immutable copy with updated parent organization reference."""
        res_parent = (
            parent_org_id
            if (parent_org_id is None or isinstance(parent_org_id, OrganizationID))
            else OrganizationID(parent_org_id)
        )
        if res_parent == self.id:
            raise ModelFormatError("Organization cannot be its own parent_org_id.")
        if res_parent == self.parent_org_id:
            return self
        return replace(
            self,
            parent_org_id=res_parent,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_parent(self, parent_id: OrganizationID | str | None) -> Self:
        """Alias for update_parent_org providing parity with Location.update_parent."""
        return self.update_parent_org(parent_id)

    def add_predecessor(self, predecessor_id: OrganizationID | str) -> Self:
        """Return a new immutable copy with unique predecessor organization appended."""
        res_id = (
            predecessor_id
            if isinstance(predecessor_id, OrganizationID)
            else OrganizationID(predecessor_id)
        )
        if res_id == self.id:
            raise ModelFormatError("Organization cannot reference itself in predecessor_ids.")
        if res_id in self.predecessor_ids:
            return self
        return replace(
            self,
            predecessor_ids=[*self.predecessor_ids, res_id],
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def remove_predecessor(self, predecessor_id: OrganizationID | str) -> Self:
        """Return a new immutable copy with predecessor organization removed."""
        res_id = (
            predecessor_id
            if isinstance(predecessor_id, OrganizationID)
            else OrganizationID(predecessor_id)
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

    def add_successor(self, successor_id: OrganizationID | str) -> Self:
        """Return a new immutable copy with unique successor organization appended."""
        res_id = (
            successor_id
            if isinstance(successor_id, OrganizationID)
            else OrganizationID(successor_id)
        )
        if res_id == self.id:
            raise ModelFormatError("Organization cannot reference itself in successor_ids.")
        if res_id in self.successor_ids:
            return self
        return replace(
            self,
            successor_ids=[*self.successor_ids, res_id],
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def remove_successor(self, successor_id: OrganizationID | str) -> Self:
        """Return a new immutable copy with successor organization removed."""
        res_id = (
            successor_id
            if isinstance(successor_id, OrganizationID)
            else OrganizationID(successor_id)
        )
        filtered = [sid for sid in self.successor_ids if sid != res_id]
        if len(filtered) == len(self.successor_ids):
            return self
        return replace(
            self,
            successor_ids=filtered,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_location(self, location_id: LocationID | str | None) -> Self:
        """Return a new immutable copy with updated operating jurisdiction."""
        res_loc = (
            location_id
            if (location_id is None or isinstance(location_id, LocationID))
            else LocationID(location_id)
        )
        if res_loc == self.location_id:
            return self
        return replace(
            self,
            location_id=res_loc,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_meeting_site(self, meeting_site_id: SiteID | str | None) -> Self:
        """Return a new immutable copy with updated physical meeting venue reference."""
        res_site = (
            meeting_site_id
            if (meeting_site_id is None or isinstance(meeting_site_id, SiteID))
            else SiteID(meeting_site_id)
        )
        if res_site == self.meeting_site_id:
            return self
        return replace(
            self,
            meeting_site_id=res_site,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_period(self, period: TimePeriod | None) -> Self:
        """Return a new immutable copy with updated temporal lifespan bounds."""
        if period == self.period:
            return self
        return replace(
            self,
            period=period,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_active(self, is_active: bool) -> Self:
        """Return a new immutable copy with updated operational status."""
        if is_active == self.is_active:
            return self
        return replace(
            self,
            is_active=is_active,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_urn(self, canonical_urn: str) -> Self:
        """Return a new immutable copy with updated canonical URN."""
        clean_urn = canonical_urn.strip() if canonical_urn else ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{clean_urn}'. "
                "Must match 'urn:gda:org:<namespace>'."
            )
        if clean_urn == self.canonical_urn:
            return self
        return replace(
            self,
            canonical_urn=clean_urn,
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
        """Serialize Organization entity to a dictionary payload."""
        data: dict[str, Any] = {
            "id": self.id.value,
            "name": self.name.to_dict(),
            "category": self.category.value,
            "canonical_urn": self.canonical_urn,
            "predecessor_ids": [pid.value for pid in self.predecessor_ids],
            "successor_ids": [sid.value for sid in self.successor_ids],
            "is_active": self.is_active,
            "audit": self.audit.to_dict(),
            "tombstone": self.tombstone.to_dict(),
            "notes": [n.to_dict() for n in self.notes],
        }
        if self.parent_org_id is not None:
            data["parent_org_id"] = self.parent_org_id.value
        if self.location_id is not None:
            data["location_id"] = self.location_id.value
        if self.meeting_site_id is not None:
            data["meeting_site_id"] = self.meeting_site_id.value
        if self.period is not None:
            data["period"] = self.period.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Organization:
        """Deserialize a dictionary payload into an immutable Organization entity."""
        if not isinstance(data, dict):
            raise ModelFormatError("Organization payload must be a dictionary.")

        raw_id = data.get("id")
        if not raw_id:
            raise ModelFormatError("Missing required field 'id' for Organization.")

        raw_name = data.get("name")
        if not raw_name:
            raise ModelFormatError("Missing required field 'name' for Organization.")

        raw_category = data.get("category")
        if not raw_category:
            raise ModelFormatError("Missing required field 'category' for Organization.")

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

        audit_payload = data.get("audit")
        audit_obj = AuditStamp.from_dict(audit_payload) if isinstance(audit_payload, dict) else None

        tombstone_payload = data.get("tombstone")
        tombstone_obj = (
            Tombstone.from_dict(tombstone_payload, id_cls=OrganizationID)
            if isinstance(tombstone_payload, dict)
            else None
        )

        notes_payload = data.get("notes", [])
        notes_list = [Note.from_dict(n) for n in notes_payload if isinstance(n, dict)]

        raw_parent = data.get("parent_org_id")
        raw_loc = data.get("location_id")
        raw_site = data.get("meeting_site_id")

        return cls.create(
            org_id=str(raw_id),
            name=resolved_name,
            category=str(raw_category),
            canonical_urn=str(data.get("canonical_urn", "")),
            parent_org_id=str(raw_parent) if raw_parent else None,
            predecessor_ids=data.get("predecessor_ids"),
            successor_ids=data.get("successor_ids"),
            location_id=str(raw_loc) if raw_loc else None,
            meeting_site_id=str(raw_site) if raw_site else None,
            audit=audit_obj,
            tombstone=tombstone_obj,
            notes=notes_list,
            period=resolved_period,
            is_active=bool(data.get("is_active", True)),
        )

    def to_json(self) -> str:
        """Serialize Organization entity to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Organization:
        """Deserialize a JSON string directly into an Organization instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse Organization JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Return concise human-readable string representation of the organization entity."""
        return f"{self.canonical_name} [{self.category.value}] ({self.id.value})"

    def __repr__(self) -> str:
        return (
            f"Organization(id={self.id!r}, canonical_name={self.canonical_name!r}, "
            f"category={self.category!r}, parent_org_id={self.parent_org_id!r})"
        )


OrganizationEntityModel = Organization
