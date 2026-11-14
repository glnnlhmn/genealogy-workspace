"""Path: src/gda/model/land/grant.py

Sovereign land grants, patents, land warrants, bounty land claims, and metes-and-bounds surveys.

Operational Role:
    Defines LandGrantRecord (extending SourceRecord) to capture primary documentary
    evidence from federal General Land Office patents, colonial and state proprietary
    grants, military bounty land warrants, homestead certificates, and official
    cadastral surveys (aligned with schemas/sources/land_deed.schema.json).
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.land import LandGrantBasis
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone
from gda.model.land.deed import LandParcel

__version__ = "1.0.0+build.2"

__all__ = [
    "LandGrantRecord",
]

_GRANT_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.LAND,
        SourceRecordCategory.PROPERTY,
        SourceRecordCategory.LEGAL,
        SourceRecordCategory.MILITARY,
    }
)

_GRANT_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.PATENT,
        SourceRecordType.WARRANT,
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


def _parse_grant_basis(raw: LandGrantBasis | str) -> LandGrantBasis:
    """Resolve LandGrantBasis by enum instance, exact value, or uppercase member name."""
    if isinstance(raw, LandGrantBasis):
        return raw
    token = str(raw).strip().upper()
    for member in LandGrantBasis:
        if token in (member.name, member.value):
            return member
    raise ModelFormatError(f"Invalid LandGrantBasis value: '{raw}'.")


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class LandGrantRecord(SourceRecord):
    """Primary archival record documenting a sovereign land patent, warrant, or survey."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.LAND,
        description="High-level archival domain category (LAND, PROPERTY, LEGAL, MILITARY).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.PATENT,
        description="Specific public-domain grant classification (PATENT, WARRANT, SURVEY).",
    )
    issuing_authority: str = Field(
        ...,
        description="Verbatim sovereign, colonial, state, or federal granting authority.",
    )
    instrument_locator: str = Field(
        ...,
        description="Primary archival call number, patent volume/page, or warrant locator.",
    )
    patentee_name_raw: str = Field(
        ...,
        description="Verbatim name of the patentee, warrantee, or primary claimant.",
    )
    parcel: LandParcel = Field(
        ...,
        description="Granted or surveyed parcel with acreage, boundaries, and neighbors.",
    )
    land_office_raw: str | None = Field(
        default=None,
        description="Verbatim local land office or secretary's office name.",
    )
    office_location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the issuing land office.",
    )
    patent_or_warrant_number: str | None = Field(
        default=None,
        description="Official patent, warrant, or survey serial number.",
    )
    certificate_or_entry_number: str | None = Field(
        default=None,
        description="Final certificate, cash entry, or homestead application number.",
    )
    grant_basis: LandGrantBasis | None = Field(
        default=None,
        description="Statutory or customary basis (CASH_ENTRY, HOMESTEAD, BOUNTY_LAND, PREEMPTION, PROPRIETARY_GRANT, OTHER).",
    )
    military_service_reference: str | None = Field(
        default=None,
        description="Verbatim military unit, war, or bounty act citation if bounty land.",
    )
    patentee_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the patentee or warrantee.",
    )
    assignee_name_raw: str | None = Field(
        default=None,
        description="Verbatim name of assignee if warrant was transferred before patenting.",
    )
    assignee_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the assignee if linked.",
    )
    surveyor_or_chain_carriers: tuple[str, ...] = Field(
        default=(),
        description="Ordered tuple of county/deputy surveyor and sworn chain-carrier names.",
    )
    date_warrant_or_entry: EventDate | None = Field(
        default=None,
        description="Date the warrant was issued or the land office entry was filed.",
    )
    date_surveyed: EventDate | None = Field(
        default=None,
        description="Date the tract was surveyed on the ground.",
    )
    date_patented: EventDate | None = Field(
        default=None,
        description="Date the final patent or royal/proprietary grant was sealed.",
    )
    aliquot_description: str | None = Field(
        default=None,
        description="Public Land Survey System (PLSS) aliquot part, section, township, and range.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _GRANT_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _GRANT_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, and required string hygiene."""
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

        for field_name in ("issuing_authority", "instrument_locator", "patentee_name_raw"):
            raw_val = getattr(self, field_name)
            cleaned = raw_val.strip()
            if not cleaned:
                raise ModelFormatError(
                    f"{self.__class__.__name__} '{field_name}' cannot be empty or whitespace."
                )
            if cleaned != raw_val:
                object.__setattr__(self, field_name, cleaned)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        issuing_authority: str,
        instrument_locator: str,
        patentee_name_raw: str,
        parcel: LandParcel | dict[str, Any],
        record_category: SourceRecordCategory | str = SourceRecordCategory.LAND,
        record_type: SourceRecordType | str = SourceRecordType.PATENT,
        land_office_raw: str | None = None,
        office_location_id: LocationID | str | None = None,
        patent_or_warrant_number: str | None = None,
        certificate_or_entry_number: str | None = None,
        grant_basis: LandGrantBasis | str | None = None,
        military_service_reference: str | None = None,
        patentee_id: IndividualID | str | None = None,
        assignee_name_raw: str | None = None,
        assignee_id: IndividualID | str | None = None,
        surveyor_or_chain_carriers: list[str] | tuple[str, ...] | None = None,
        date_warrant_or_entry: EventDate | dict[str, Any] | str | None = None,
        date_surveyed: EventDate | dict[str, Any] | str | None = None,
        date_patented: EventDate | dict[str, Any] | str | None = None,
        aliquot_description: str | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> LandGrantRecord:
        """Factory constructor instantiating a validated LandGrantRecord."""
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
        res_basis = _parse_grant_basis(grant_basis) if grant_basis is not None else None
        res_pat_id = (
            patentee_id
            if (patentee_id is None or isinstance(patentee_id, IndividualID))
            else IndividualID(patentee_id)
        )
        res_ass_id = (
            assignee_id
            if (assignee_id is None or isinstance(assignee_id, IndividualID))
            else IndividualID(assignee_id)
        )
        res_warrant_dt = (
            _deserialize_event_date(date_warrant_or_entry, "date_warrant_or_entry")
            if date_warrant_or_entry is not None
            else None
        )
        res_survey_dt = (
            _deserialize_event_date(date_surveyed, "date_surveyed")
            if date_surveyed is not None
            else None
        )
        res_patent_dt = (
            _deserialize_event_date(date_patented, "date_patented")
            if date_patented is not None
            else None
        )
        resolved_parcel = parcel if isinstance(parcel, LandParcel) else LandParcel.from_dict(parcel)

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
            issuing_authority=issuing_authority,
            instrument_locator=instrument_locator,
            patentee_name_raw=patentee_name_raw,
            parcel=resolved_parcel,
            land_office_raw=land_office_raw,
            office_location_id=res_office_loc,
            patent_or_warrant_number=patent_or_warrant_number,
            certificate_or_entry_number=certificate_or_entry_number,
            grant_basis=res_basis,
            military_service_reference=military_service_reference,
            patentee_id=res_pat_id,
            assignee_name_raw=assignee_name_raw,
            assignee_id=res_ass_id,
            surveyor_or_chain_carriers=tuple(surveyor_or_chain_carriers or ()),
            date_warrant_or_entry=res_warrant_dt,
            date_surveyed=res_survey_dt,
            date_patented=res_patent_dt,
            aliquot_description=aliquot_description,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize LandGrantRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "issuing_authority": self.issuing_authority,
                "instrument_locator": self.instrument_locator,
                "patentee_name_raw": self.patentee_name_raw,
                "parcel": self.parcel.to_dict(),
                "surveyor_or_chain_carriers": list(self.surveyor_or_chain_carriers),
            }
        )
        if self.land_office_raw is not None:
            data["land_office_raw"] = self.land_office_raw
        if self.office_location_id is not None:
            data["office_location_id"] = str(self.office_location_id)
        if self.patent_or_warrant_number is not None:
            data["patent_or_warrant_number"] = self.patent_or_warrant_number
        if self.certificate_or_entry_number is not None:
            data["certificate_or_entry_number"] = self.certificate_or_entry_number
        if self.grant_basis is not None:
            data["grant_basis"] = self.grant_basis.value
        if self.military_service_reference is not None:
            data["military_service_reference"] = self.military_service_reference
        if self.patentee_id is not None:
            data["patentee_id"] = str(self.patentee_id)
        if self.assignee_name_raw is not None:
            data["assignee_name_raw"] = self.assignee_name_raw
        if self.assignee_id is not None:
            data["assignee_id"] = str(self.assignee_id)
        if self.date_warrant_or_entry is not None:
            data["date_warrant_or_entry"] = self.date_warrant_or_entry.to_dict()
        if self.date_surveyed is not None:
            data["date_surveyed"] = self.date_surveyed.to_dict()
        if self.date_patented is not None:
            data["date_patented"] = self.date_patented.to_dict()
        if self.aliquot_description is not None:
            data["aliquot_description"] = self.aliquot_description
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LandGrantRecord:
        """Deserialize a dictionary payload into a LandGrantRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("LandGrantRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        authority = data.get("issuing_authority")
        locator = data.get("instrument_locator")
        patentee = data.get("patentee_name_raw")
        raw_parcel = data.get("parcel")

        if not all(
            (sid, raw_urn, desc, rep, audit_payload, authority, locator, patentee, raw_parcel)
        ):
            raise ModelFormatError(
                "LandGrantRecord requires source_id, source_urn, description, repository_id, "
                "audit, issuing_authority, instrument_locator, patentee_name_raw, and parcel."
            )

        if isinstance(audit_payload, AuditStamp):
            audit_obj = audit_payload
        elif isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )
        else:
            raise ModelFormatError("LandGrantRecord audit must be an AuditStamp or dictionary.")

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

        raw_surveyors = data.get("surveyor_or_chain_carriers", [])
        if not isinstance(raw_surveyors, (list, tuple)):
            raise ModelFormatError(
                "LandGrantRecord 'surveyor_or_chain_carriers' must be a list or tuple."
            )

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            issuing_authority=str(authority),
            instrument_locator=str(locator),
            patentee_name_raw=str(patentee),
            parcel=raw_parcel,
            record_category=data.get("record_category", SourceRecordCategory.LAND),
            record_type=data.get("record_type", SourceRecordType.PATENT),
            land_office_raw=data.get("land_office_raw"),
            office_location_id=data.get("office_location_id"),
            patent_or_warrant_number=data.get("patent_or_warrant_number"),
            certificate_or_entry_number=data.get("certificate_or_entry_number"),
            grant_basis=data.get("grant_basis"),
            military_service_reference=data.get("military_service_reference"),
            patentee_id=data.get("patentee_id"),
            assignee_name_raw=data.get("assignee_name_raw"),
            assignee_id=data.get("assignee_id"),
            surveyor_or_chain_carriers=list(raw_surveyors),
            date_warrant_or_entry=data.get("date_warrant_or_entry"),
            date_surveyed=data.get("date_surveyed"),
            date_patented=data.get("date_patented"),
            aliquot_description=data.get("aliquot_description"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return (
            f"LandGrantRecord [{self.record_type.value}] "
            f"{self.patentee_name_raw} ({self.instrument_locator})"
        )
