"""Path: src/gda/model/source/vital/baptism.py

Ecclesiastical baptismal, christening, and cradle roll record models.

Operational Role:
    Defines BaptismRecord extending SourceRecord to capture primary documentary
    evidence from church baptismal registers, baptismal certificates, christening
    entries, and cradle rolls (aligned with schemas/sources/church_baptism.schema.json).
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.core import Sex
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    MediaID,
    OrganizationID,
    RepositoryID,
    SiteID,
    SourceID,
)
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.1"

__all__ = [
    "BaptismRecord",
]

_BAPTISM_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.CHURCH,
        SourceRecordCategory.VITAL,
    }
)

_BAPTISM_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.BAPTISM_REGISTER,
        SourceRecordType.BAPTISM_CERTIFICATE,
        SourceRecordType.CHRISTENING_ENTRY,
        SourceRecordType.CRADLE_ROLL,
    }
)


def _deserialize_event_date(raw: Any, field_name: str) -> EventDate:
    """Coerce an EventDate instance, dictionary, or compact date string."""
    if isinstance(raw, EventDate):
        return raw
    if isinstance(raw, (dict, str)):
        return EventDate.from_dict(raw)
    raise ModelFormatError(f"Invalid '{field_name}' payload: expected EventDate, dict, or str.")


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class BaptismRecord(SourceRecord):
    """Primary archival record documenting an ecclesiastical baptism, christening, or dedication."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.CHURCH,
        description="High-level archival domain category (CHURCH or VITAL).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.BAPTISM_REGISTER,
        description="Specific baptismal documentary record classification.",
    )
    church_name_raw: str = Field(
        ...,
        description="Verbatim name of the church, parish, or congregation.",
    )
    baptized_name_raw: str = Field(
        ...,
        description="Verbatim full name of the baptized or christened individual.",
    )
    date_of_baptism: EventDate = Field(
        ...,
        description="Recorded date of baptism or christening ceremony.",
    )
    church_org_id: OrganizationID | None = Field(
        default=None,
        description="Resolved canonical OrganizationID of the congregation if linked.",
    )
    church_site_id: SiteID | None = Field(
        default=None,
        description="Resolved canonical SiteID of the church building if linked.",
    )
    location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID of the parish jurisdiction.",
    )
    denomination: str | None = Field(
        default=None,
        description="Religious denomination or tradition (e.g., 'Congregational', 'Roman Catholic').",
    )
    volume_title: str | None = Field(
        default=None,
        description="Title or designation of the parish register book.",
    )
    register_locator: str | None = Field(
        default=None,
        description="Page, folio, or entry number inside the parish register.",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the baptized person if linked.",
    )
    sex: Sex | None = Field(
        default=None,
        description="Recorded biological sex if noted in the baptismal register.",
    )
    date_of_birth: EventDate | None = Field(
        default=None,
        description="Date of birth stated in the baptismal entry.",
    )
    place_of_birth_raw: str | None = Field(
        default=None,
        description="Verbatim birthplace or parental residence recorded in the register.",
    )
    officiant_name_raw: str | None = Field(
        default=None,
        description="Verbatim name and title of the officiating clergy member.",
    )
    father_name_raw: str | None = Field(
        default=None,
        description="Verbatim father's name recorded in the register.",
    )
    mother_name_raw: str | None = Field(
        default=None,
        description="Verbatim mother's name (maiden or married) recorded in the register.",
    )
    sponsors_or_godparents: list[str] = Field(
        default_factory=list,
        description="Verbatim names of godparents, sponsors, or witnesses.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _BAPTISM_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _BAPTISM_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, church name, and baptized name boundaries."""
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

        for field_name in ("church_name_raw", "baptized_name_raw"):
            raw_val = getattr(self, field_name)
            clean_val = raw_val.strip()
            if not clean_val:
                raise ModelFormatError(
                    f"{self.__class__.__name__} '{field_name}' cannot be empty or whitespace."
                )
            if clean_val != raw_val:
                object.__setattr__(self, field_name, clean_val)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        church_name_raw: str,
        baptized_name_raw: str,
        date_of_baptism: EventDate | dict[str, Any] | str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.CHURCH,
        record_type: SourceRecordType | str = SourceRecordType.BAPTISM_REGISTER,
        church_org_id: OrganizationID | str | None = None,
        church_site_id: SiteID | str | None = None,
        location_id: LocationID | str | None = None,
        denomination: str | None = None,
        volume_title: str | None = None,
        register_locator: str | None = None,
        individual_id: IndividualID | str | None = None,
        sex: Sex | str | None = None,
        date_of_birth: EventDate | dict[str, Any] | str | None = None,
        place_of_birth_raw: str | None = None,
        officiant_name_raw: str | None = None,
        father_name_raw: str | None = None,
        mother_name_raw: str | None = None,
        sponsors_or_godparents: list[str] | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> BaptismRecord:
        """Factory constructor instantiating a validated BaptismRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = (
            source_urn if isinstance(source_urn, ArchivalURN) else SourceURN(str(source_urn))
        )
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
        res_org_id = (
            church_org_id
            if (church_org_id is None or isinstance(church_org_id, OrganizationID))
            else OrganizationID(church_org_id)
        )
        res_site_id = (
            church_site_id
            if (church_site_id is None or isinstance(church_site_id, SiteID))
            else SiteID(church_site_id)
        )
        res_loc_id = (
            location_id
            if (location_id is None or isinstance(location_id, LocationID))
            else LocationID(location_id)
        )
        res_ind_id = (
            individual_id
            if (individual_id is None or isinstance(individual_id, IndividualID))
            else IndividualID(individual_id)
        )
        res_sex = sex if (sex is None or isinstance(sex, Sex)) else Sex.from_input(str(sex))

        res_bap_date = _deserialize_event_date(date_of_baptism, "date_of_baptism")
        res_dob = (
            _deserialize_event_date(date_of_birth, "date_of_birth")
            if date_of_birth is not None
            else None
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
            church_name_raw=church_name_raw,
            baptized_name_raw=baptized_name_raw,
            date_of_baptism=res_bap_date,
            church_org_id=res_org_id,
            church_site_id=res_site_id,
            location_id=res_loc_id,
            denomination=denomination,
            volume_title=volume_title,
            register_locator=register_locator,
            individual_id=res_ind_id,
            sex=res_sex,
            date_of_birth=res_dob,
            place_of_birth_raw=place_of_birth_raw,
            officiant_name_raw=officiant_name_raw,
            father_name_raw=father_name_raw,
            mother_name_raw=mother_name_raw,
            sponsors_or_godparents=(
                list(sponsors_or_godparents) if sponsors_or_godparents is not None else []
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize BaptismRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "church_name_raw": self.church_name_raw,
                "baptized_name_raw": self.baptized_name_raw,
                "date_of_baptism": self.date_of_baptism.to_dict(),
                "sponsors_or_godparents": list(self.sponsors_or_godparents),
            }
        )
        if self.church_org_id is not None:
            data["church_org_id"] = str(self.church_org_id)
        if self.church_site_id is not None:
            data["church_site_id"] = str(self.church_site_id)
        if self.location_id is not None:
            data["location_id"] = str(self.location_id)
        if self.denomination is not None:
            data["denomination"] = self.denomination
        if self.volume_title is not None:
            data["volume_title"] = self.volume_title
        if self.register_locator is not None:
            data["register_locator"] = self.register_locator
        if self.individual_id is not None:
            data["individual_id"] = str(self.individual_id)
        if self.sex is not None:
            data["sex"] = self.sex.value
        if self.date_of_birth is not None:
            data["date_of_birth"] = self.date_of_birth.to_dict()
        if self.place_of_birth_raw is not None:
            data["place_of_birth_raw"] = self.place_of_birth_raw
        if self.officiant_name_raw is not None:
            data["officiant_name_raw"] = self.officiant_name_raw
        if self.father_name_raw is not None:
            data["father_name_raw"] = self.father_name_raw
        if self.mother_name_raw is not None:
            data["mother_name_raw"] = self.mother_name_raw
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaptismRecord:
        """Deserialize a dictionary payload into a BaptismRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("BaptismRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        church_name = data.get("church_name_raw")
        baptized_name = data.get("baptized_name_raw")
        raw_bap_date = data.get("date_of_baptism")

        if not all(
            (
                sid,
                raw_urn,
                desc,
                rep,
                audit_payload,
                church_name,
                baptized_name,
                raw_bap_date,
            )
        ):
            raise ModelFormatError(
                "BaptismRecord requires source_id, source_urn, description, repository_id, "
                "audit, church_name_raw, baptized_name_raw, and date_of_baptism."
            )

        if isinstance(audit_payload, AuditStamp):
            audit_obj = audit_payload
        elif isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )
        else:
            raise ModelFormatError("BaptismRecord audit must be an AuditStamp or dictionary.")

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
            church_name_raw=str(church_name),
            baptized_name_raw=str(baptized_name),
            date_of_baptism=raw_bap_date,
            record_category=data.get("record_category", SourceRecordCategory.CHURCH),
            record_type=data.get("record_type", SourceRecordType.BAPTISM_REGISTER),
            church_org_id=data.get("church_org_id"),
            church_site_id=data.get("church_site_id"),
            location_id=data.get("location_id"),
            denomination=data.get("denomination"),
            volume_title=data.get("volume_title"),
            register_locator=data.get("register_locator"),
            individual_id=data.get("individual_id"),
            sex=data.get("sex"),
            date_of_birth=data.get("date_of_birth"),
            place_of_birth_raw=data.get("place_of_birth_raw"),
            officiant_name_raw=data.get("officiant_name_raw"),
            father_name_raw=data.get("father_name_raw"),
            mother_name_raw=data.get("mother_name_raw"),
            sponsors_or_godparents=data.get("sponsors_or_godparents"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"BaptismRecord [{self.baptized_name_raw} @ {self.church_name_raw}] ({self.date_of_baptism})"
