"""Path: src/gda/model/land/deed.py

Historical land deeds, indentures, quitclaims, mortgages, sheriff's deeds, and dower releases.

Operational Role:
    Defines DeedParty (grantor or grantee entry), LandParcel (tract, acreage,
    metes-and-bounds, neighboring landowners, and chain-of-title back-reference),
    and LandDeedRecord (extending SourceRecord) to capture primary documentary
    evidence from real-property conveyances and recorder books (aligned with
    schemas/sources/land_deed.schema.json).
"""

from __future__ import annotations

import json
import re
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.land import DeedPartyRole
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.2"

__all__ = [
    "DeedParty",
    "LandDeedRecord",
    "LandParcel",
]

_DEED_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.LAND,
        SourceRecordCategory.LEGAL,
        SourceRecordCategory.PROPERTY,
    }
)

_DEED_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.DEED_INDENTURE,
        SourceRecordType.QUITCLAIM_DEED,
        SourceRecordType.MORTGAGE,
        SourceRecordType.SHERIFF_DEED,
        SourceRecordType.RELEASE_DOWER,
        SourceRecordType.WARRANT,
        SourceRecordType.PATENT,
        SourceRecordType.SURVEY,
    }
)

_LAND_URN_PATTERN: re.Pattern[str] = re.compile(r"^URN:LAND:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$")


def _resolve_land_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into ArchivalURN (URN:LAND:...) or SourceURN (URN:SRC:...)."""
    if isinstance(raw, ArchivalURN):
        return raw
    token = str(raw).strip()
    if token.startswith("URN:LAND:"):
        if not _LAND_URN_PATTERN.match(token):
            raise ModelFormatError(
                f"Invalid Land URN syntax: '{token}'. "
                "Must match 'URN:LAND:<YEAR>:<JURISDICTION>:<LOCATOR>'."
            )
        return ArchivalURN(token)
    return SourceURN(token)


def _deserialize_event_date(raw: Any, field_name: str) -> EventDate:
    """Coerce an EventDate instance, dictionary, or compact date string."""
    if isinstance(raw, EventDate):
        return raw
    if isinstance(raw, (dict, str)):
        return EventDate.from_dict(raw)
    raise ModelFormatError(f"Invalid '{field_name}' payload: expected EventDate, dict, or str.")


def _parse_party_role(raw: DeedPartyRole | str) -> DeedPartyRole:
    """Resolve DeedPartyRole by enum instance, exact value, or uppercase member name."""
    if isinstance(raw, DeedPartyRole):
        return raw
    token = str(raw).strip().upper()
    for member in DeedPartyRole:
        if token in (member.name, member.value):
            return member
    raise ModelFormatError(f"Invalid DeedPartyRole value: '{raw}'.")


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class DeedParty(IntrospectableMixin):
    """Single grantor or grantee named in a real-property conveyance."""

    full_name: str = Field(
        ...,
        description="Verbatim or standardized full name of the grantor or grantee.",
    )
    party_role: DeedPartyRole = Field(
        default=DeedPartyRole.GRANTOR,
        description="Conveyance capacity (DeedPartyRole.GRANTOR or DeedPartyRole.GRANTEE).",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID if linked to a person entity.",
    )
    residence_raw: str | None = Field(
        default=None,
        description="Verbatim town, township, or county of residence stated in the deed.",
    )
    residence_location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the party's residence.",
    )
    relationship_to_grantee: str | None = Field(
        default=None,
        description="Verbatim kinship or fiduciary role stated in the instrument (e.g., 'wife', 'heirs').",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty full_name hygiene."""
        clean_name = self.full_name.strip()
        if not clean_name:
            raise ModelFormatError("DeedParty 'full_name' cannot be empty or whitespace.")
        if clean_name != self.full_name:
            object.__setattr__(self, "full_name", clean_name)

    @classmethod
    def create(
        cls,
        full_name: str,
        party_role: DeedPartyRole | str = DeedPartyRole.GRANTOR,
        individual_id: IndividualID | str | None = None,
        residence_raw: str | None = None,
        residence_location_id: LocationID | str | None = None,
        relationship_to_grantee: str | None = None,
    ) -> DeedParty:
        """Factory constructor instantiating a validated DeedParty."""
        res_ind = (
            individual_id
            if (individual_id is None or isinstance(individual_id, IndividualID))
            else IndividualID(individual_id)
        )
        res_loc = (
            residence_location_id
            if (residence_location_id is None or isinstance(residence_location_id, LocationID))
            else LocationID(residence_location_id)
        )
        return cls(
            full_name=full_name,
            party_role=_parse_party_role(party_role),
            individual_id=res_ind,
            residence_raw=residence_raw,
            residence_location_id=res_loc,
            relationship_to_grantee=relationship_to_grantee,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize DeedParty to a dictionary."""
        data: dict[str, Any] = {
            "full_name": self.full_name,
            "party_role": self.party_role.value,
        }
        if self.individual_id is not None:
            data["individual_id"] = str(self.individual_id)
        if self.residence_raw is not None:
            data["residence_raw"] = self.residence_raw
        if self.residence_location_id is not None:
            data["residence_location_id"] = str(self.residence_location_id)
        if self.relationship_to_grantee is not None:
            data["relationship_to_grantee"] = self.relationship_to_grantee
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeedParty:
        """Deserialize a dictionary payload into a DeedParty."""
        if not isinstance(data, dict):
            raise ModelFormatError("DeedParty payload must be a dictionary.")
        name = data.get("full_name")
        if name is None:
            raise ModelFormatError("DeedParty requires 'full_name'.")
        return cls.create(
            full_name=str(name),
            party_role=data.get("party_role", DeedPartyRole.GRANTOR),
            individual_id=data.get("individual_id"),
            residence_raw=data.get("residence_raw"),
            residence_location_id=data.get("residence_location_id"),
            relationship_to_grantee=data.get("relationship_to_grantee"),
        )

    def to_json(self) -> str:
        """Serialize DeedParty to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> DeedParty:
        """Deserialize a JSON string directly into a DeedParty."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse DeedParty JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.party_role.value})"


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class LandParcel(IntrospectableMixin):
    """Tract of real property, acreage, metes-and-bounds, and abutting neighbors."""

    location_raw: str = Field(
        ...,
        description="Verbatim township, lot, range, watercourse, or jurisdictional description.",
    )
    location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the parcel's civil jurisdiction.",
    )
    tract_name: str | None = Field(
        default=None,
        description="Historical tract, patent, or farm name if stated.",
    )
    acreage_raw: str | None = Field(
        default=None,
        description="Verbatim area measurement (e.g., '80 acres, 40 rods').",
    )
    acreage_numeric: float | None = Field(
        default=None,
        ge=0.0,
        description="Normalized decimal acreage for aggregation.",
    )
    metes_and_bounds_summary: str | None = Field(
        default=None,
        description="Abstract of courses, distances, monuments, and survey boundaries.",
    )
    neighboring_landowners: tuple[str, ...] = Field(
        default=(),
        description="Ordered tuple of abutting landowner names cited in boundary calls.",
    )
    prior_deed_recital: str | None = Field(
        default=None,
        description="Chain-of-title back-reference recital (grantor, date, or book/page).",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty location_raw hygiene."""
        clean_loc = self.location_raw.strip()
        if not clean_loc:
            raise ModelFormatError("LandParcel 'location_raw' cannot be empty or whitespace.")
        if clean_loc != self.location_raw:
            object.__setattr__(self, "location_raw", clean_loc)

    @classmethod
    def create(
        cls,
        location_raw: str,
        location_id: LocationID | str | None = None,
        tract_name: str | None = None,
        acreage_raw: str | None = None,
        acreage_numeric: float | int | None = None,
        metes_and_bounds_summary: str | None = None,
        neighboring_landowners: list[str] | tuple[str, ...] | None = None,
        prior_deed_recital: str | None = None,
    ) -> LandParcel:
        """Factory constructor instantiating a validated LandParcel."""
        res_loc = (
            location_id
            if (location_id is None or isinstance(location_id, LocationID))
            else LocationID(location_id)
        )
        res_acres = float(acreage_numeric) if acreage_numeric is not None else None
        return cls(
            location_raw=location_raw,
            location_id=res_loc,
            tract_name=tract_name,
            acreage_raw=acreage_raw,
            acreage_numeric=res_acres,
            metes_and_bounds_summary=metes_and_bounds_summary,
            neighboring_landowners=tuple(neighboring_landowners or ()),
            prior_deed_recital=prior_deed_recital,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize LandParcel to a dictionary."""
        data: dict[str, Any] = {
            "location_raw": self.location_raw,
            "neighboring_landowners": list(self.neighboring_landowners),
        }
        if self.location_id is not None:
            data["location_id"] = str(self.location_id)
        if self.tract_name is not None:
            data["tract_name"] = self.tract_name
        if self.acreage_raw is not None:
            data["acreage_raw"] = self.acreage_raw
        if self.acreage_numeric is not None:
            data["acreage_numeric"] = self.acreage_numeric
        if self.metes_and_bounds_summary is not None:
            data["metes_and_bounds_summary"] = self.metes_and_bounds_summary
        if self.prior_deed_recital is not None:
            data["prior_deed_recital"] = self.prior_deed_recital
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LandParcel:
        """Deserialize a dictionary payload into a LandParcel."""
        if not isinstance(data, dict):
            raise ModelFormatError("LandParcel payload must be a dictionary.")
        loc = data.get("location_raw")
        if loc is None:
            raise ModelFormatError("LandParcel requires 'location_raw'.")
        raw_neighbors = data.get("neighboring_landowners", [])
        if not isinstance(raw_neighbors, (list, tuple)):
            raise ModelFormatError("LandParcel 'neighboring_landowners' must be a list or tuple.")
        return cls.create(
            location_raw=str(loc),
            location_id=data.get("location_id"),
            tract_name=data.get("tract_name"),
            acreage_raw=data.get("acreage_raw"),
            acreage_numeric=data.get("acreage_numeric"),
            metes_and_bounds_summary=data.get("metes_and_bounds_summary"),
            neighboring_landowners=list(raw_neighbors),
            prior_deed_recital=data.get("prior_deed_recital"),
        )

    def to_json(self) -> str:
        """Serialize LandParcel to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> LandParcel:
        """Deserialize a JSON string directly into a LandParcel."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse LandParcel JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        if self.tract_name:
            return f"{self.tract_name} ({self.location_raw})"
        return self.location_raw


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class LandDeedRecord(SourceRecord):
    """Primary archival record documenting a land deed, indenture, mortgage, or release."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.LAND,
        description="High-level archival domain category (LAND, LEGAL, PROPERTY).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.DEED_INDENTURE,
        description="Specific conveyance instrument classification.",
    )
    office_title: str = Field(
        ...,
        description="Verbatim title of the Registry of Deeds or Recorder of Deeds office.",
    )
    recording_locator: str = Field(
        ...,
        description="Primary archival call number, deed book/page, or instrument locator.",
    )
    date_written: EventDate = Field(
        ...,
        description="Date the deed or conveyance instrument was signed and sealed.",
    )
    grantors: tuple[DeedParty, ...] = Field(
        ...,
        description="Ordered tuple of one or more grantors conveying title or interest.",
    )
    grantees: tuple[DeedParty, ...] = Field(
        ...,
        description="Ordered tuple of one or more grantees receiving title or interest.",
    )
    parcel: LandParcel = Field(
        ...,
        description="Primary tract of real property conveyed by this instrument.",
    )
    office_location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the recording office.",
    )
    recorder_or_deputy: str | None = Field(
        default=None,
        description="Name of the Register of Deeds, Recorder, or Deputy Clerk.",
    )
    deed_book: str | None = Field(
        default=None,
        description="Recorded deed book or liber designation.",
    )
    page_number: str | None = Field(
        default=None,
        description="Recorded folio or page number within the deed book.",
    )
    instrument_number: str | None = Field(
        default=None,
        description="Official sequential instrument or reception number.",
    )
    date_acknowledged: EventDate | None = Field(
        default=None,
        description="Date the grantors acknowledged execution before a Justice or Notary.",
    )
    date_recorded: EventDate | None = Field(
        default=None,
        description="Date the instrument was received and entered in the public registry.",
    )
    consideration_amount: str | None = Field(
        default=None,
        description="Verbatim monetary or nominal consideration stated in the deed.",
    )
    dower_relinquished: bool | None = Field(
        default=None,
        description="True if a spouse's separate dower release examination was recorded.",
    )
    additional_parcels: tuple[LandParcel, ...] = Field(
        default=(),
        description="Optional tuple of secondary tracts conveyed in the same deed.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _DEED_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _DEED_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, required strings, and non-empty grantors/grantees."""
        super().__post_init__()

        if self.record_category not in self.ALLOWED_CATEGORIES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_category in "
                f"{sorted(c.value for c in self.ALLOWED_CATEGORIES)}, "
                f"got '{self.record_category.value}'."
            )

        if self.record_type not in self.ALLOWED_RECORD_TYPES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_type in "
                f"{sorted(t.value for t in self.ALLOWED_RECORD_TYPES)}, "
                f"got '{self.record_type.value}'."
            )

        for field_name in ("office_title", "recording_locator"):
            raw_val = getattr(self, field_name)
            cleaned = raw_val.strip()
            if not cleaned:
                raise ModelFormatError(
                    f"{self.__class__.__name__} '{field_name}' cannot be empty or whitespace."
                )
            if cleaned != raw_val:
                object.__setattr__(self, field_name, cleaned)

        if not self.grantors:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires at least one grantor DeedParty."
            )
        if not self.grantees:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires at least one grantee DeedParty."
            )

    @property
    def grantor_count(self) -> int:
        """Return count of grantors in this conveyance."""
        return len(self.grantors)

    @property
    def grantee_count(self) -> int:
        """Return count of grantees in this conveyance."""
        return len(self.grantees)

    @property
    def all_parcels(self) -> tuple[LandParcel, ...]:
        """Return tuple combining primary parcel and any additional parcels."""
        return (self.parcel, *self.additional_parcels)

    def flatten_parties(self) -> tuple[dict[str, Any], ...]:
        """Flatten deed and primary parcel context with every grantor and grantee."""
        header: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "office_title": self.office_title,
            "recording_locator": self.recording_locator,
            "date_written": str(self.date_written),
            "parcel_location_raw": self.parcel.location_raw,
            "consideration_amount": self.consideration_amount,
        }
        return tuple({**header, **party.to_dict()} for party in (*self.grantors, *self.grantees))

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        office_title: str,
        recording_locator: str,
        date_written: EventDate | dict[str, Any] | str,
        grantors: list[DeedParty | dict[str, Any]] | tuple[DeedParty, ...],
        grantees: list[DeedParty | dict[str, Any]] | tuple[DeedParty, ...],
        parcel: LandParcel | dict[str, Any],
        record_category: SourceRecordCategory | str = SourceRecordCategory.LAND,
        record_type: SourceRecordType | str = SourceRecordType.DEED_INDENTURE,
        office_location_id: LocationID | str | None = None,
        recorder_or_deputy: str | None = None,
        deed_book: str | None = None,
        page_number: str | None = None,
        instrument_number: str | None = None,
        date_acknowledged: EventDate | dict[str, Any] | str | None = None,
        date_recorded: EventDate | dict[str, Any] | str | None = None,
        consideration_amount: str | None = None,
        dower_relinquished: bool | None = None,
        additional_parcels: list[LandParcel | dict[str, Any]]
        | tuple[LandParcel, ...]
        | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> LandDeedRecord:
        """Factory constructor instantiating a validated LandDeedRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_land_urn(source_urn)
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        res_cat = (
            record_category
            if isinstance(record_category, SourceRecordCategory)
            else SourceRecordCategory(str(record_category).strip().upper())
        )
        res_type = (
            record_type
            if isinstance(record_type, SourceRecordType)
            else SourceRecordType(str(record_type).strip().upper())
        )
        res_office_loc = (
            office_location_id
            if (office_location_id is None or isinstance(office_location_id, LocationID))
            else LocationID(office_location_id)
        )
        res_written = _deserialize_event_date(date_written, "date_written")
        res_ack = (
            _deserialize_event_date(date_acknowledged, "date_acknowledged")
            if date_acknowledged is not None
            else None
        )
        res_rec = (
            _deserialize_event_date(date_recorded, "date_recorded")
            if date_recorded is not None
            else None
        )

        resolved_grantors: tuple[DeedParty, ...] = tuple(
            p
            if isinstance(p, DeedParty)
            else DeedParty.from_dict(
                {**p, "party_role": p.get("party_role", DeedPartyRole.GRANTOR)}
            )
            for p in grantors
        )
        resolved_grantees: tuple[DeedParty, ...] = tuple(
            p
            if isinstance(p, DeedParty)
            else DeedParty.from_dict(
                {**p, "party_role": p.get("party_role", DeedPartyRole.GRANTEE)}
            )
            for p in grantees
        )
        resolved_parcel = parcel if isinstance(parcel, LandParcel) else LandParcel.from_dict(parcel)
        resolved_extra: tuple[LandParcel, ...] = tuple(
            p if isinstance(p, LandParcel) else LandParcel.from_dict(p)
            for p in (additional_parcels or ())
        )

        resolved_audit = audit if audit is not None else AuditStamp.now()
        resolved_media = [m if isinstance(m, MediaID) else MediaID(m) for m in (media_ids or [])]

        return cls(
            source_id=resolved_sid,
            source_urn=resolved_urn,
            record_category=res_cat,
            record_type=res_type,
            description=description.strip() if isinstance(description, str) else description,
            repository_id=resolved_rep,
            audit=resolved_audit,
            media_ids=resolved_media,
            associated_people=associated_people or [],
            tombstone=tombstone,
            office_title=office_title,
            recording_locator=recording_locator,
            date_written=res_written,
            grantors=resolved_grantors,
            grantees=resolved_grantees,
            parcel=resolved_parcel,
            office_location_id=res_office_loc,
            recorder_or_deputy=recorder_or_deputy,
            deed_book=deed_book,
            page_number=page_number,
            instrument_number=instrument_number,
            date_acknowledged=res_ack,
            date_recorded=res_rec,
            consideration_amount=consideration_amount,
            dower_relinquished=dower_relinquished,
            additional_parcels=resolved_extra,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize LandDeedRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "office_title": self.office_title,
                "recording_locator": self.recording_locator,
                "date_written": self.date_written.to_dict(),
                "grantors": [g.to_dict() for g in self.grantors],
                "grantees": [g.to_dict() for g in self.grantees],
                "parcel": self.parcel.to_dict(),
                "additional_parcels": [p.to_dict() for p in self.additional_parcels],
            }
        )
        if self.office_location_id is not None:
            data["office_location_id"] = str(self.office_location_id)
        if self.recorder_or_deputy is not None:
            data["recorder_or_deputy"] = self.recorder_or_deputy
        if self.deed_book is not None:
            data["deed_book"] = self.deed_book
        if self.page_number is not None:
            data["page_number"] = self.page_number
        if self.instrument_number is not None:
            data["instrument_number"] = self.instrument_number
        if self.date_acknowledged is not None:
            data["date_acknowledged"] = self.date_acknowledged.to_dict()
        if self.date_recorded is not None:
            data["date_recorded"] = self.date_recorded.to_dict()
        if self.consideration_amount is not None:
            data["consideration_amount"] = self.consideration_amount
        if self.dower_relinquished is not None:
            data["dower_relinquished"] = self.dower_relinquished
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LandDeedRecord:
        """Deserialize a dictionary payload into a LandDeedRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("LandDeedRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        office = data.get("office_title")
        locator = data.get("recording_locator")
        raw_written = data.get("date_written")
        raw_grantors = data.get("grantors")
        raw_grantees = data.get("grantees")
        raw_parcel = data.get("parcel")

        if not all(
            (
                sid,
                raw_urn,
                desc,
                rep,
                audit_payload,
                office,
                locator,
                raw_written,
                raw_grantors,
                raw_grantees,
                raw_parcel,
            )
        ):
            raise ModelFormatError(
                "LandDeedRecord requires source_id, source_urn, description, repository_id, "
                "audit, office_title, recording_locator, date_written, grantors, grantees, and parcel."
            )

        if not isinstance(raw_grantors, (list, tuple)):
            raise ModelFormatError("LandDeedRecord 'grantors' must be a list or tuple.")
        if not isinstance(raw_grantees, (list, tuple)):
            raise ModelFormatError("LandDeedRecord 'grantees' must be a list or tuple.")

        raw_extra = data.get("additional_parcels", [])
        if not isinstance(raw_extra, (list, tuple)):
            raise ModelFormatError("LandDeedRecord 'additional_parcels' must be a list or tuple.")

        if isinstance(audit_payload, AuditStamp):
            audit_obj = audit_payload
        elif isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )
        else:
            raise ModelFormatError("LandDeedRecord audit must be an AuditStamp or dictionary.")

        tombstone_payload = data.get("tombstone")
        tombstone_obj: Tombstone[SourceID] | None = None
        if isinstance(tombstone_payload, dict):
            raw_sup = tombstone_payload.get("superseded_by")
            sup_id = (
                raw_sup
                if (raw_sup is None or isinstance(raw_sup, SourceID))
                else SourceID(str(raw_sup))
            )
            tombstone_obj = Tombstone[SourceID](
                is_deprecated=tombstone_payload.get("is_deprecated", False),
                deprecated_at=(
                    IsoTimestamp(tombstone_payload["deprecated_at"])
                    if tombstone_payload.get("deprecated_at")
                    else None
                ),
                superseded_by=sup_id,
            )

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            office_title=str(office),
            recording_locator=str(locator),
            date_written=raw_written,
            grantors=list(raw_grantors),
            grantees=list(raw_grantees),
            parcel=raw_parcel,
            record_category=data.get("record_category", SourceRecordCategory.LAND),
            record_type=data.get("record_type", SourceRecordType.DEED_INDENTURE),
            office_location_id=data.get("office_location_id"),
            recorder_or_deputy=data.get("recorder_or_deputy"),
            deed_book=data.get("deed_book"),
            page_number=data.get("page_number"),
            instrument_number=data.get("instrument_number"),
            date_acknowledged=data.get("date_acknowledged"),
            date_recorded=data.get("date_recorded"),
            consideration_amount=data.get("consideration_amount"),
            dower_relinquished=data.get("dower_relinquished"),
            additional_parcels=list(raw_extra),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        first_grantor = self.grantors[0].full_name
        first_grantee = self.grantees[0].full_name
        return (
            f"LandDeedRecord [{self.record_type.value}] "
            f"{first_grantor} -> {first_grantee} ({self.recording_locator})"
        )
