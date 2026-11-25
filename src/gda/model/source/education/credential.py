"""Path: src/gda/model/source/education/credential.py

Historical academic diplomas, graduation certificates, yearbooks, and school transcripts.

Operational Role:
    Defines AcademicCredentialRecord (extending SourceRecord) to capture primary
    documentary evidence from school diplomas, graduation certificates, commencement
    programs, yearbook pages, class rosters, and transcript reports (aligned with
    schemas/sources/academic_credential.schema.json).
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, cast

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums import coerce_enum
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import EducationLevel
from gda.core.errors import ModelFormatError
from gda.core.types import URN_REGEXES
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.4"

__all__ = [
    "AcademicCredentialRecord",
]

_EDUCATION_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.EDUCATION,
    }
)

_EDUCATION_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.DIPLOMA,
        SourceRecordType.GRADUATION_CERTIFICATE,
        SourceRecordType.YEARBOOK_PAGE,
        SourceRecordType.COMMENCEMENT_PROGRAM,
        SourceRecordType.CLASS_ROSTER,
        SourceRecordType.TRANSCRIPT_REPORT,
    }
)

_DIPLOMA_URN_PATTERN: re.Pattern[str] = URN_REGEXES["DIPLOMA"]


def _resolve_diploma_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into ArchivalURN (URN:DIPLOMA:...) or SourceURN (URN:SRC:...)."""
    if isinstance(raw, ArchivalURN):
        return raw
    token = str(raw).strip()
    if token.startswith("URN:DIPLOMA:"):
        if not _DIPLOMA_URN_PATTERN.match(token):
            raise ModelFormatError(
                f"Invalid Diploma URN syntax: '{token}'. "
                "Must match 'URN:DIPLOMA:<YEAR>:<JURISDICTION>:<LOCATOR>'."
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


def _parse_education_level(raw: EducationLevel | str) -> EducationLevel:
    """Resolve EducationLevel by enum instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(EducationLevel, raw, field_name="education_level")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid EducationLevel value: '{raw}'.") from err


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class AcademicCredentialRecord(SourceRecord):
    """Primary archival record documenting a diploma, graduation certificate, or school record."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.EDUCATION,
        description="High-level archival domain category (EDUCATION).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.DIPLOMA,
        description="Specific educational document classification.",
    )
    institution_name_raw: str = Field(
        ...,
        description="Verbatim name of the school, academy, college, or university.",
    )
    subject_name_raw: str = Field(
        ...,
        description="Verbatim full name of the graduate, student, or credential recipient.",
    )
    date_issued_or_published: EventDate = Field(
        ...,
        description="Date the diploma, certificate, roster, or yearbook was issued.",
    )
    education_level: EducationLevel | None = Field(
        default=None,
        description="Educational tier (ELEM, HS, COLL, GRAD, VOC, OTHER).",
    )
    institution_location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the school or campus.",
    )
    subject_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the credential subject.",
    )
    degree_or_credential: str | None = Field(
        default=None,
        description="Verbatim degree, diploma title, or course of study conferred.",
    )
    graduation_year: int | None = Field(
        default=None,
        ge=1600,
        le=2100,
        description="Four-digit graduation or class year.",
    )
    publication_title: str | None = Field(
        default=None,
        description="Title of yearbook, catalog, or commencement program if published.",
    )
    page_or_plate: str | None = Field(
        default=None,
        description="Page, folio, or plate locator within the publication or ledger.",
    )
    credential_note: str | None = Field(
        default=None,
        description="Additional archival note on honors, signatories, or provenance.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _EDUCATION_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _EDUCATION_RECORD_TYPES

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

        for field_name in ("institution_name_raw", "subject_name_raw"):
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
        institution_name_raw: str,
        subject_name_raw: str,
        date_issued_or_published: EventDate | dict[str, Any] | str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.EDUCATION,
        record_type: SourceRecordType | str = SourceRecordType.DIPLOMA,
        education_level: EducationLevel | str | None = None,
        institution_location_id: LocationID | str | None = None,
        subject_id: IndividualID | str | None = None,
        degree_or_credential: str | None = None,
        graduation_year: int | None = None,
        publication_title: str | None = None,
        page_or_plate: str | None = None,
        credential_note: str | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> AcademicCredentialRecord:
        """Factory constructor instantiating a validated AcademicCredentialRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_diploma_urn(source_urn)
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        res_cat = coerce_enum(SourceRecordCategory, record_category, field_name="record_category")
        res_type = coerce_enum(SourceRecordType, record_type, field_name="record_type")
        res_level = _parse_education_level(education_level) if education_level is not None else None
        res_inst_loc = (
            institution_location_id
            if (institution_location_id is None or isinstance(institution_location_id, LocationID))
            else LocationID(institution_location_id)
        )
        res_sub_id = (
            subject_id
            if (subject_id is None or isinstance(subject_id, IndividualID))
            else IndividualID(subject_id)
        )
        res_date = _deserialize_event_date(date_issued_or_published, "date_issued_or_published")

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
            institution_name_raw=institution_name_raw,
            subject_name_raw=subject_name_raw,
            date_issued_or_published=res_date,
            education_level=res_level,
            institution_location_id=res_inst_loc,
            subject_id=res_sub_id,
            degree_or_credential=degree_or_credential,
            graduation_year=graduation_year,
            publication_title=publication_title,
            page_or_plate=page_or_plate,
            credential_note=credential_note,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize AcademicCredentialRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "institution_name_raw": self.institution_name_raw,
                "subject_name_raw": self.subject_name_raw,
                "date_issued_or_published": self.date_issued_or_published.to_dict(),
            }
        )
        if self.education_level is not None:
            data["education_level"] = self.education_level.value
        if self.institution_location_id is not None:
            data["institution_location_id"] = str(self.institution_location_id)
        if self.subject_id is not None:
            data["subject_id"] = str(self.subject_id)
        if self.degree_or_credential is not None:
            data["degree_or_credential"] = self.degree_or_credential
        if self.graduation_year is not None:
            data["graduation_year"] = self.graduation_year
        if self.publication_title is not None:
            data["publication_title"] = self.publication_title
        if self.page_or_plate is not None:
            data["page_or_plate"] = self.page_or_plate
        if self.credential_note is not None:
            data["credential_note"] = self.credential_note
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AcademicCredentialRecord:
        """Deserialize a dictionary payload into an AcademicCredentialRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("AcademicCredentialRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        inst = data.get("institution_name_raw")
        subj = data.get("subject_name_raw")
        raw_dt = data.get("date_issued_or_published")

        if not all((sid, raw_urn, desc, rep, audit_payload, inst, subj, raw_dt)):
            raise ModelFormatError(
                "AcademicCredentialRecord requires source_id, source_urn, description, "
                "repository_id, audit, institution_name_raw, subject_name_raw, and "
                "date_issued_or_published."
            )

        if not isinstance(audit_payload, (AuditStamp, dict)):
            raise ModelFormatError(
                "AcademicCredentialRecord audit must be an AuditStamp or dictionary."
            )
        audit_obj = AuditStamp.from_dict(audit_payload)

        tombstone_payload = data.get("tombstone")
        tombstone_obj = (
            Tombstone.from_dict(tombstone_payload, id_cls=SourceID)
            if isinstance(tombstone_payload, dict)
            else None
        )

        raw_grad_year = data.get("graduation_year")
        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            institution_name_raw=str(inst),
            subject_name_raw=str(subj),
            date_issued_or_published=cast(Any, raw_dt),
            record_category=data.get("record_category", SourceRecordCategory.EDUCATION),
            record_type=data.get("record_type", SourceRecordType.DIPLOMA),
            education_level=data.get("education_level"),
            institution_location_id=data.get("institution_location_id"),
            subject_id=data.get("subject_id"),
            degree_or_credential=data.get("degree_or_credential"),
            graduation_year=int(raw_grad_year) if raw_grad_year is not None else None,
            publication_title=data.get("publication_title"),
            page_or_plate=data.get("page_or_plate"),
            credential_note=data.get("credential_note"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return (
            f"AcademicCredentialRecord [{self.record_type.value}] "
            f"{self.subject_name_raw} - {self.institution_name_raw}"
        )
