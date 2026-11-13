"""Path: src/gda/model/vital/birth.py

Civil and hospital birth certificate and birth register domain models.

Operational Role:
    Defines BirthRecord extending SourceRecord to capture primary documentary
    evidence from civil birth certificates, delayed birth certificates, hospital
    birth certificates, stillborn records, and town/civil birth register entries
    (aligned with schemas/sources/birth_certificate.schema.json).
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.core import Sex
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import BirthPlurality, VitalModifier
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN, VitalCertificateUrn
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.2"

__all__ = [
    "BirthRecord",
]

_BIRTH_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.BIRTH_CERTIFICATE,
        SourceRecordType.DELAYED_BIRTH,
        SourceRecordType.REGISTER_ENTRY,
        SourceRecordType.STILLBORN_RECORD,
        SourceRecordType.HOSPITAL_CERTIFICATE,
    }
)


def _resolve_vital_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into VitalCertificateUrn or SourceURN."""
    if isinstance(raw, ArchivalURN):
        return raw
    token = str(raw).strip()
    if token.startswith("URN:VITAL:"):
        return VitalCertificateUrn(token)
    return SourceURN(token)


def _deserialize_event_date(raw: Any, field_name: str) -> EventDate:
    """Coerce an EventDate instance, dictionary, or compact date string."""
    if isinstance(raw, EventDate):
        return raw
    if isinstance(raw, (dict, str)):
        return EventDate.from_dict(raw)
    raise ModelFormatError(f"Invalid '{field_name}' payload: expected EventDate, dict, or str.")


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class BirthRecord(SourceRecord):
    """Primary archival record documenting a birth, delayed birth, or stillbirth."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.VITAL,
        description="High-level archival domain category (restricted to VITAL).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.BIRTH_CERTIFICATE,
        description="Specific birth documentary record classification.",
    )
    child_name_raw: str = Field(
        ...,
        description="Verbatim full name of the child as inscribed on the birth record.",
    )
    date_of_birth: EventDate = Field(
        ...,
        description="Recorded date of birth assertion.",
    )
    place_of_birth_raw: str = Field(
        ...,
        description="Verbatim place of birth (town, county, state, or hospital).",
    )
    child_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the child if linked.",
    )
    sex: Sex = Field(
        default=Sex.UNKNOWN,
        description="Recorded biological sex of the child.",
    )
    plurality: BirthPlurality = Field(
        default=BirthPlurality.SINGLE,
        description="Birth plurality (Single, Twin, Triplet, Quadruplet).",
    )
    birth_order: str | None = Field(
        default=None,
        description="Verbatim birth order or number of children born to mother.",
    )
    is_stillborn: bool = Field(
        default=False,
        description="True if the record documents a stillbirth.",
    )
    vital_modifier: VitalModifier | None = Field(
        default=None,
        description="Optional vital condition modifier (STILLBORN, ILLEGITIMATE, POSTHUMOUS, etc.).",
    )
    time_of_birth: str | None = Field(
        default=None,
        description="Verbatim hour/minute of birth if recorded.",
    )
    place_of_birth_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the birthplace jurisdiction.",
    )
    legitimacy: bool | None = Field(
        default=None,
        description="Recorded legitimacy indicator if stated on the certificate.",
    )
    certificate_number: str | None = Field(
        default=None,
        description="Official state, county, or local certificate/file number.",
    )
    registration_district: str | None = Field(
        default=None,
        description="Registration district, town, or ward designation.",
    )
    date_filed: EventDate | None = Field(
        default=None,
        description="Date the birth return or delayed affidavit was filed.",
    )
    father_name_raw: str | None = Field(
        default=None,
        description="Verbatim father's name recorded on the birth entry.",
    )
    mother_maiden_name_raw: str | None = Field(
        default=None,
        description="Verbatim mother's maiden or full name recorded on the birth entry.",
    )

    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _BIRTH_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, and non-empty string boundaries."""
        super().__post_init__()

        if self.record_category is not SourceRecordCategory.VITAL:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_category VITAL, "
                f"got '{self.record_category.value}'."
            )

        if self.record_type not in self.ALLOWED_RECORD_TYPES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_type in "
                f"{sorted(t.value for t in self.ALLOWED_RECORD_TYPES)}, "
                f"got '{self.record_type.value}'."
            )

        clean_child = self.child_name_raw.strip()
        if not clean_child:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'child_name_raw' cannot be empty or whitespace."
            )
        if clean_child != self.child_name_raw:
            object.__setattr__(self, "child_name_raw", clean_child)

        clean_place = self.place_of_birth_raw.strip()
        if not clean_place:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'place_of_birth_raw' cannot be empty or whitespace."
            )
        if clean_place != self.place_of_birth_raw:
            object.__setattr__(self, "place_of_birth_raw", clean_place)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        child_name_raw: str,
        date_of_birth: EventDate | dict[str, Any] | str,
        place_of_birth_raw: str,
        record_type: SourceRecordType | str = SourceRecordType.BIRTH_CERTIFICATE,
        child_id: IndividualID | str | None = None,
        sex: Sex | str = Sex.UNKNOWN,
        plurality: BirthPlurality | str = BirthPlurality.SINGLE,
        birth_order: str | None = None,
        is_stillborn: bool = False,
        vital_modifier: VitalModifier | str | None = None,
        time_of_birth: str | None = None,
        place_of_birth_id: LocationID | str | None = None,
        legitimacy: bool | None = None,
        certificate_number: str | None = None,
        registration_district: str | None = None,
        date_filed: EventDate | dict[str, Any] | str | None = None,
        father_name_raw: str | None = None,
        mother_maiden_name_raw: str | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> BirthRecord:
        """Factory constructor instantiating a validated BirthRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_vital_urn(source_urn)
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        res_type = (
            record_type
            if isinstance(record_type, SourceRecordType)
            else SourceRecordType(str(record_type).strip().upper())
        )
        resolved_child_id = (
            child_id
            if (child_id is None or isinstance(child_id, IndividualID))
            else IndividualID(child_id)
        )
        resolved_place_id = (
            place_of_birth_id
            if (place_of_birth_id is None or isinstance(place_of_birth_id, LocationID))
            else LocationID(place_of_birth_id)
        )
        resolved_sex = sex if isinstance(sex, Sex) else Sex.from_input(str(sex))
        resolved_plurality = (
            plurality
            if isinstance(plurality, BirthPlurality)
            else BirthPlurality(str(plurality).strip().capitalize())
        )
        resolved_modifier = (
            vital_modifier
            if (vital_modifier is None or isinstance(vital_modifier, VitalModifier))
            else VitalModifier(str(vital_modifier).strip().upper())
        )

        resolved_dob = _deserialize_event_date(date_of_birth, "date_of_birth")
        resolved_filed = (
            _deserialize_event_date(date_filed, "date_filed") if date_filed is not None else None
        )
        resolved_audit = audit if audit is not None else AuditStamp.now()
        resolved_media = [m if isinstance(m, MediaID) else MediaID(m) for m in (media_ids or [])]

        return cls(
            source_id=resolved_sid,
            source_urn=resolved_urn,
            record_category=SourceRecordCategory.VITAL,
            record_type=res_type,
            description=description.strip() if isinstance(description, str) else description,
            repository_id=resolved_rep,
            audit=resolved_audit,
            media_ids=resolved_media,
            associated_people=associated_people or [],
            tombstone=tombstone,
            child_name_raw=child_name_raw,
            date_of_birth=resolved_dob,
            place_of_birth_raw=place_of_birth_raw,
            child_id=resolved_child_id,
            sex=resolved_sex,
            plurality=resolved_plurality,
            birth_order=birth_order,
            is_stillborn=is_stillborn,
            vital_modifier=resolved_modifier,
            time_of_birth=time_of_birth,
            place_of_birth_id=resolved_place_id,
            legitimacy=legitimacy,
            certificate_number=certificate_number,
            registration_district=registration_district,
            date_filed=resolved_filed,
            father_name_raw=father_name_raw,
            mother_maiden_name_raw=mother_maiden_name_raw,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize BirthRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "child_name_raw": self.child_name_raw,
                "date_of_birth": self.date_of_birth.to_dict(),
                "place_of_birth_raw": self.place_of_birth_raw,
                "sex": self.sex.value,
                "plurality": self.plurality.value,
                "is_stillborn": self.is_stillborn,
            }
        )
        if self.child_id is not None:
            data["child_id"] = str(self.child_id)
        if self.birth_order is not None:
            data["birth_order"] = self.birth_order
        if self.vital_modifier is not None:
            data["vital_modifier"] = self.vital_modifier.value
        if self.time_of_birth is not None:
            data["time_of_birth"] = self.time_of_birth
        if self.place_of_birth_id is not None:
            data["place_of_birth_id"] = str(self.place_of_birth_id)
        if self.legitimacy is not None:
            data["legitimacy"] = self.legitimacy
        if self.certificate_number is not None:
            data["certificate_number"] = self.certificate_number
        if self.registration_district is not None:
            data["registration_district"] = self.registration_district
        if self.date_filed is not None:
            data["date_filed"] = self.date_filed.to_dict()
        if self.father_name_raw is not None:
            data["father_name_raw"] = self.father_name_raw
        if self.mother_maiden_name_raw is not None:
            data["mother_maiden_name_raw"] = self.mother_maiden_name_raw
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BirthRecord:
        """Deserialize a dictionary payload into a BirthRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("BirthRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        child_name = data.get("child_name_raw")
        raw_dob = data.get("date_of_birth")
        place_raw = data.get("place_of_birth_raw")

        if not all((sid, raw_urn, desc, rep, audit_payload, child_name, raw_dob, place_raw)):
            raise ModelFormatError(
                "BirthRecord requires source_id, source_urn, description, repository_id, "
                "audit, child_name_raw, date_of_birth, and place_of_birth_raw."
            )

        raw_cat = data.get("record_category", SourceRecordCategory.VITAL.value)
        if str(raw_cat).strip().upper() != SourceRecordCategory.VITAL.value:
            raise ModelFormatError(f"BirthRecord requires record_category VITAL, got '{raw_cat}'.")

        if isinstance(audit_payload, AuditStamp):
            audit_obj = audit_payload
        elif isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )
        else:
            raise ModelFormatError("BirthRecord audit must be an AuditStamp or dictionary.")

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
            child_name_raw=str(child_name),
            date_of_birth=raw_dob,
            place_of_birth_raw=str(place_raw),
            record_type=data.get("record_type", SourceRecordType.BIRTH_CERTIFICATE),
            child_id=data.get("child_id"),
            sex=data.get("sex", Sex.UNKNOWN),
            plurality=data.get("plurality", BirthPlurality.SINGLE),
            birth_order=data.get("birth_order"),
            is_stillborn=bool(data.get("is_stillborn", False)),
            vital_modifier=data.get("vital_modifier"),
            time_of_birth=data.get("time_of_birth"),
            place_of_birth_id=data.get("place_of_birth_id"),
            legitimacy=data.get("legitimacy"),
            certificate_number=data.get("certificate_number"),
            registration_district=data.get("registration_district"),
            date_filed=data.get("date_filed"),
            father_name_raw=data.get("father_name_raw"),
            mother_maiden_name_raw=data.get("mother_maiden_name_raw"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"BirthRecord [{self.child_name_raw}] ({self.date_of_birth})"
