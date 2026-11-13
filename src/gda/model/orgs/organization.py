"""Path: src/gda/model/orgs/organization.py

Voluntary association, fraternal society, religious body, and civic organization models.

Operational Role:
    Defines Organization representing human associations and institutions that
    individuals join or affiliate with (e.g., fraternal lodges, church congregations,
    men's choirs, labor guilds, veterans' posts, and civic societies). Inherits
    lifecycle management, audit timestamps, soft-deprecation tombstones, and embedded
    Note collections from BaseEntity[OrganizationID]. Incorporates NameThing for
    temporal naming evolution, OrganizationCategory, optional parent_org_id for
    chapter-to-grand-body hierarchies, optional LocationID and meeting SiteID
    references, TimePeriod bounds, explicit in-memory dirty tracking (_dirty), and
    full dictionary/JSON serialization parity.
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
from gda.core.enums.orgs import OrganizationCategory
from gda.core.enums.vital import HistoricNameType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, NoteID, OrganizationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.entity import BaseEntity
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.1"

__all__ = [
    "Organization",
    "OrganizationEntityModel",
]

_ORG_ID_PATTERN: re.Pattern[str] = re.compile(r"^ORG-\d{6}$")
_ORG_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:org:[a-z0-9_:\-]+$")


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
        """Enforce domain invariants and structural boundary guards."""
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
    def is_dirty(self) -> bool:
        """Return True if entity has unpersisted in-memory modifications."""
        return self._dirty

    @property
    def aliases(self) -> list[str]:
        """Forward colloquial naming aliases from naming value object."""
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
        location_id: LocationID | str | None = None,
        meeting_site_id: SiteID | str | None = None,
        audit: AuditStamp | None = None,
        tombstone: Tombstone[OrganizationID] | None = None,
        notes: list[Note] | None = None,
        period: TimePeriod | None = None,
        is_active: bool = True,
    ) -> Organization:
        """Factory constructor instantiating a validated Organization entity."""
        resolved_id = org_id if isinstance(org_id, OrganizationID) else OrganizationID(org_id)

        if isinstance(name, NameThing):
            resolved_name = name
        elif isinstance(name, str):
            clean_str = name.strip()
            if not clean_str:
                raise ModelFormatError("Organization 'name' cannot be empty or whitespace.")
            resolved_name = NameThing.create(raw=clean_str, canonical=clean_str)
        else:
            raise TypeError(
                f"Organization 'name' must be an instance of NameThing or str, "
                f"got {type(name).__name__}."
            )

        if isinstance(category, OrganizationCategory):
            resolved_cat = category
        elif isinstance(category, str):
            try:
                resolved_cat = OrganizationCategory(category.strip().upper())
            except ValueError as exc:
                raise ModelFormatError(
                    f"Invalid OrganizationCategory value: '{category}'."
                ) from exc
        else:
            raise TypeError(
                f"Organization 'category' must be OrganizationCategory or str, "
                f"got {type(category).__name__}."
            )

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

        now_ts = IsoTimestamp(utc_now_iso())
        resolved_audit = (
            audit if audit is not None else AuditStamp(created_at=now_ts, updated_at=now_ts)
        )
        resolved_tombstone = tombstone if tombstone is not None else Tombstone[OrganizationID]()
        resolved_notes = list(notes) if notes is not None else []

        return cls(
            id=resolved_id,
            name=resolved_name,
            category=resolved_cat,
            canonical_urn=canonical_urn.strip() if canonical_urn else "",
            parent_org_id=resolved_parent,
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
        if isinstance(name, NameThing):
            new_name = name
        elif isinstance(name, str):
            clean_str = name.strip()
            if not clean_str:
                raise ModelFormatError("Organization 'name' cannot be empty or whitespace.")
            new_name = NameThing.create(raw=clean_str, canonical=clean_str)
        else:
            raise TypeError(
                f"Organization 'name' must be an instance of NameThing or str, "
                f"got {type(name).__name__}."
            )
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
        if isinstance(category, OrganizationCategory):
            res_cat = category
        elif isinstance(category, str):
            try:
                res_cat = OrganizationCategory(category.strip().upper())
            except ValueError as exc:
                raise ModelFormatError(
                    f"Invalid OrganizationCategory value: '{category}'."
                ) from exc
        else:
            raise TypeError(
                f"Organization 'category' must be OrganizationCategory or str, "
                f"got {type(category).__name__}."
            )
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
        if res_parent == self.parent_org_id:
            return self
        return replace(
            self,
            parent_org_id=res_parent,
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
            "is_active": self.is_active,
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
        audit_obj: AuditStamp | None = None
        if isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )

        tombstone_payload = data.get("tombstone")
        tombstone_obj: Tombstone[OrganizationID] | None = None
        if isinstance(tombstone_payload, dict):
            tombstone_obj = Tombstone[OrganizationID](
                is_deprecated=tombstone_payload.get("is_deprecated", False),
                deprecated_at=(
                    IsoTimestamp(tombstone_payload["deprecated_at"])
                    if tombstone_payload.get("deprecated_at")
                    else None
                ),
                superseded_by=(
                    OrganizationID(tombstone_payload["superseded_by"])
                    if tombstone_payload.get("superseded_by")
                    else None
                ),
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
