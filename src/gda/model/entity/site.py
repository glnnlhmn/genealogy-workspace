"""Path: src/gda/model/entity/site.py

Physical venue and archival site entity model implementations.

Operational Role:
    Defines Site representing physical venues, structures, cemeteries, churches,
    and repositories situated within civil jurisdictions. Inherits lifecycle
    management, audit timestamps, soft-deprecation tombstones, and embedded Note
    collections from BaseEntity[SiteID]. Incorporates NameThing for structured
    temporal naming evolution, SiteType for controlled classification, Address
    for physical location, Coordinates from gda.model.base.geo, explicit in-memory
    dirty tracking (_dirty), and full dictionary/JSON serialization parity.
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
from gda.core.enums.site import SiteType
from gda.core.enums.vital import HistoricNameType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, NoteID, SiteID
from gda.model.base.address import Address
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.entity import BaseEntity
from gda.model.base.geo import Coordinates
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone

__version__ = "2.0.0+build.1"

__all__ = [
    "Site",
    "SiteEntityModel",
]

_SITE_ID_PATTERN: re.Pattern[str] = re.compile(r"^SID-\d{6}$")
_SITE_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:site:[a-z0-9_:\-]+$")


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class Site(BaseEntity[SiteID]):
    """Primary physical venue, facility, or landmark entity model."""

    name: NameThing = Field(
        ...,
        description="Standardized naming value object containing canonical and historic forms.",
    )
    category: SiteType = Field(
        ..., description="Controlled functional classification of the physical venue."
    )
    canonical_urn: str = Field(
        ...,
        description="Semantic deterministic lookup URN (e.g., 'urn:gda:site:us:nh:bow:cemetery').",
    )
    location_id: LocationID = Field(
        ..., description="Foreign key reference to governing civil jurisdiction."
    )
    address: Address | None = Field(
        default=None, description="Optional physical or street-level postal address."
    )
    coordinates: Coordinates | None = Field(
        default=None,
        description="Geographic coordinates marking site entrance or centroid.",
    )
    period: TimePeriod | None = Field(
        default=None,
        description="Structured temporal bounds spanning establishment to closure.",
    )
    is_active: bool = Field(
        default=True,
        description="Indicates whether the facility is currently extant or operational.",
    )
    _dirty: bool = Field(
        default=False,
        description="True if entity has unpersisted state changes in working memory.",
    )

    _ID_PATTERN: ClassVar[re.Pattern[str]] = _SITE_ID_PATTERN
    _URN_PATTERN: ClassVar[re.Pattern[str]] = _SITE_URN_PATTERN

    def __post_init__(self) -> None:
        """Enforce domain invariants and structural boundary guards."""
        super().__post_init__()

        if not isinstance(self.id, SiteID):
            raise TypeError(
                f"Site 'id' must be an instance of SiteID, got {type(self.id).__name__}."
            )

        raw_id = self.id.value
        if not self._ID_PATTERN.match(raw_id):
            raise ModelFormatError(f"Invalid SiteID format: '{raw_id}'. Must match 'SID-######'.")

        clean_urn = self.canonical_urn.strip() if self.canonical_urn else ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:site:<namespace>'."
            )
        if clean_urn != self.canonical_urn:
            object.__setattr__(self, "canonical_urn", clean_urn)

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Site cannot be superseded by itself.")

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
    def date_established(self) -> EventDate | None:
        """Convenience accessor for site establishment date from period."""
        return self.period.start_date if self.period is not None else None

    @property
    def date_closed(self) -> EventDate | None:
        """Convenience accessor for site closure date from period."""
        return self.period.end_date if self.period is not None else None

    @classmethod
    def create(
        cls,
        site_id: SiteID | str,
        name: NameThing | str,
        category: SiteType | str,
        canonical_urn: str,
        location_id: LocationID | str,
        audit: AuditStamp | None = None,
        tombstone: Tombstone[SiteID] | None = None,
        notes: list[Note] | None = None,
        address: Address | None = None,
        coordinates: Coordinates | None = None,
        period: TimePeriod | None = None,
        is_active: bool = True,
    ) -> Site:
        """Factory constructor instantiating a validated Site entity."""
        resolved_id = site_id if isinstance(site_id, SiteID) else SiteID(site_id)

        if isinstance(name, NameThing):
            resolved_name = name
        elif isinstance(name, str):
            clean_str = name.strip()
            if not clean_str:
                raise ModelFormatError("Site 'name' cannot be empty or whitespace.")
            resolved_name = NameThing.create(raw=clean_str, canonical=clean_str)
        else:
            raise TypeError(
                f"Site 'name' must be an instance of NameThing or str, got {type(name).__name__}."
            )

        resolved_cat = (
            category if isinstance(category, SiteType) else SiteType(category.strip().upper())
        )
        resolved_loc = (
            location_id if isinstance(location_id, LocationID) else LocationID(location_id)
        )

        now_ts = IsoTimestamp(utc_now_iso())
        resolved_audit = (
            audit if audit is not None else AuditStamp(created_at=now_ts, updated_at=now_ts)
        )
        resolved_tombstone = tombstone if tombstone is not None else Tombstone[SiteID]()
        resolved_notes = list(notes) if notes is not None else []

        return cls(
            id=resolved_id,
            name=resolved_name,
            category=resolved_cat,
            canonical_urn=canonical_urn.strip() if canonical_urn else "",
            location_id=resolved_loc,
            audit=resolved_audit,
            tombstone=resolved_tombstone,
            notes=resolved_notes,
            address=address,
            coordinates=coordinates,
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
                raise ModelFormatError("Site 'name' cannot be empty or whitespace.")
            new_name = NameThing.create(raw=clean_str, canonical=clean_str)
        else:
            raise TypeError(
                f"Site 'name' must be an instance of NameThing or str, got {type(name).__name__}."
            )
        if new_name == self.name:
            return self
        return replace(
            self,
            name=new_name,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_category(self, category: SiteType | str) -> Self:
        """Return a new immutable copy with updated site classification."""
        res_cat = category if isinstance(category, SiteType) else SiteType(category.strip().upper())
        if res_cat == self.category:
            return self
        return replace(
            self,
            category=res_cat,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_location(self, location_id: LocationID | str) -> Self:
        """Return a new immutable copy with updated governing jurisdiction."""
        res_loc = location_id if isinstance(location_id, LocationID) else LocationID(location_id)
        if res_loc == self.location_id:
            return self
        return replace(
            self,
            location_id=res_loc,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_address(self, address: Address | None) -> Self:
        """Return a new immutable copy with updated physical street address."""
        if address == self.address:
            return self
        return replace(
            self,
            address=address,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_coordinates(self, coordinates: Coordinates | None) -> Self:
        """Return a new immutable copy with updated geospatial coordinates."""
        if coordinates == self.coordinates:
            return self
        return replace(
            self,
            coordinates=coordinates,
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
                "Must match 'urn:gda:site:<namespace>'."
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
        """Serialize Site entity to a dictionary payload."""
        data: dict[str, Any] = {
            "id": self.id.value,
            "name": self.name.to_dict(),
            "category": self.category.value,
            "canonical_urn": self.canonical_urn,
            "location_id": self.location_id.value,
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
        if self.address is not None:
            data["address"] = self.address.to_dict()
        if self.coordinates is not None:
            data["coordinates"] = self.coordinates.to_dict()
        if self.period is not None:
            data["period"] = self.period.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Site:
        """Deserialize a dictionary payload into an immutable Site entity."""
        if not isinstance(data, dict):
            raise ModelFormatError("Site payload must be a dictionary.")

        raw_id = data.get("id")
        if not raw_id:
            raise ModelFormatError("Missing required field 'id' for Site.")

        raw_name = data.get("name")
        if not raw_name:
            raise ModelFormatError("Missing required field 'name' for Site.")

        raw_category = data.get("category")
        if not raw_category:
            raise ModelFormatError("Missing required field 'category' for Site.")

        raw_location_id = data.get("location_id")
        if not raw_location_id:
            raise ModelFormatError("Missing required field 'location_id' for Site.")

        resolved_name: NameThing | str = (
            NameThing.from_dict(raw_name) if isinstance(raw_name, dict) else raw_name
        )

        raw_address = data.get("address")
        resolved_address: Address | None = None
        if isinstance(raw_address, Address):
            resolved_address = raw_address
        elif isinstance(raw_address, dict):
            resolved_address = Address.from_dict(raw_address)

        raw_coords = data.get("coordinates")
        resolved_coords: Coordinates | None = None
        if isinstance(raw_coords, Coordinates):
            resolved_coords = raw_coords
        elif isinstance(raw_coords, dict):
            resolved_coords = Coordinates.from_dict(raw_coords)

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
        tombstone_obj: Tombstone[SiteID] | None = None
        if isinstance(tombstone_payload, dict):
            tombstone_obj = Tombstone[SiteID](
                is_deprecated=tombstone_payload.get("is_deprecated", False),
                deprecated_at=(
                    IsoTimestamp(tombstone_payload["deprecated_at"])
                    if tombstone_payload.get("deprecated_at")
                    else None
                ),
                superseded_by=(
                    SiteID(tombstone_payload["superseded_by"])
                    if tombstone_payload.get("superseded_by")
                    else None
                ),
            )

        notes_payload = data.get("notes", [])
        notes_list = [Note.from_dict(n) for n in notes_payload if isinstance(n, dict)]

        return cls.create(
            site_id=str(raw_id),
            name=resolved_name,
            category=str(raw_category),
            canonical_urn=str(data.get("canonical_urn", "")),
            location_id=str(raw_location_id),
            audit=audit_obj,
            tombstone=tombstone_obj,
            notes=notes_list,
            address=resolved_address,
            coordinates=resolved_coords,
            period=resolved_period,
            is_active=bool(data.get("is_active", True)),
        )

    def to_json(self) -> str:
        """Serialize Site entity to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Site:
        """Deserialize a JSON string directly into a Site instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse Site JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Return concise human-readable string representation of the site entity."""
        return f"{self.canonical_name} [{self.category.value}] ({self.id.value})"

    def __repr__(self) -> str:
        return (
            f"Site(id={self.id!r}, canonical_name={self.canonical_name!r}, "
            f"category={self.category!r}, location_id={self.location_id!r})"
        )


SiteEntityModel = Site
