"""Path: src/gda/model/source/publications/periodical.py

Periodical article, school yearbook, commencement program, and published history models.

Operational Role:
    Defines PublicationEntry (single enumerated subject entry on a yearbook page,
    alumni roster, or biographical compilation) and PeriodicalArticleRecord
    (extending SourceRecord) supporting both standalone periodical articles /
    biographical sketches and collection-wide multi-subject pages with tabular
    flatten_entries() projection.
"""

from __future__ import annotations

import json
from typing import Any, ClassVar, cast

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums import coerce_enum
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import EducationLevel
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import PUB_CODE_REGEX
from gda.model.atom.id import IndividualID, MediaID, OrganizationID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.3"

__all__ = [
    "PeriodicalArticleRecord",
    "PublicationEntry",
]

_PERIODICAL_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.EDUCATION,
        SourceRecordCategory.NARRATIVE,
        SourceRecordCategory.NEWS,
        SourceRecordCategory.FRATERNAL,
        SourceRecordCategory.CHURCH,
        SourceRecordCategory.OTHER,
    }
)

_PERIODICAL_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.YEARBOOK_PAGE,
        SourceRecordType.COMMENCEMENT_PROGRAM,
        SourceRecordType.CLASS_ROSTER,
        SourceRecordType.MEMOIR,
        SourceRecordType.MISC,
        SourceRecordType.PHOTO,
    }
)


def _deserialize_event_date(raw: Any, field_name: str) -> EventDate:
    """Coerce an EventDate instance, dictionary, or compact date string."""
    if isinstance(raw, EventDate):
        return raw
    if isinstance(raw, (dict, str)):
        return EventDate.from_dict(raw)
    raise ModelFormatError(f"Invalid '{field_name}' payload: expected EventDate, dict, or str.")


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class PublicationEntry(IntrospectableMixin):
    """Single enumerated subject row on a yearbook page, alumni directory, or history."""

    line_number: int = Field(
        ...,
        ge=1,
        description="1-based sequence or entry number on the printed page.",
    )
    subject_name_verbatim: str = Field(
        ...,
        description="Verbatim transcribed name of the student, alumnus, or biographical subject.",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID if linked to a person entity.",
    )
    role_or_class_raw: str | None = Field(
        default=None,
        description="Verbatim class year, degree, office, or biographical role.",
    )
    page_or_plate: str | None = Field(
        default=None,
        description="Specific page, portrait plate, or column locator for this subject.",
    )
    remarks_raw: str | None = Field(
        default=None,
        description="Verbatim residence, hometown, honors, or biographical snippet.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty verbatim subject name hygiene."""
        cleaned = self.subject_name_verbatim.strip()
        if not cleaned:
            raise ModelFormatError(
                "PublicationEntry 'subject_name_verbatim' cannot be empty or whitespace.",
                details={"line_number": self.line_number},
            )
        if cleaned != self.subject_name_verbatim:
            object.__setattr__(self, "subject_name_verbatim", cleaned)

    @classmethod
    def create(
        cls,
        line_number: int,
        subject_name_verbatim: str,
        individual_id: IndividualID | str | None = None,
        role_or_class_raw: str | None = None,
        page_or_plate: str | None = None,
        remarks_raw: str | None = None,
    ) -> PublicationEntry:
        """Factory constructor instantiating a validated PublicationEntry."""
        res_ind = (
            individual_id
            if (individual_id is None or isinstance(individual_id, IndividualID))
            else IndividualID(individual_id)
        )
        return cls(
            line_number=line_number,
            subject_name_verbatim=subject_name_verbatim,
            individual_id=res_ind,
            role_or_class_raw=role_or_class_raw,
            page_or_plate=page_or_plate,
            remarks_raw=remarks_raw,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize PublicationEntry to a dictionary."""
        data: dict[str, Any] = {
            "line_number": self.line_number,
            "subject_name_verbatim": self.subject_name_verbatim,
        }
        if self.individual_id is not None:
            data["individual_id"] = str(self.individual_id)
        if self.role_or_class_raw is not None:
            data["role_or_class_raw"] = self.role_or_class_raw
        if self.page_or_plate is not None:
            data["page_or_plate"] = self.page_or_plate
        if self.remarks_raw is not None:
            data["remarks_raw"] = self.remarks_raw
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PublicationEntry:
        """Deserialize a dictionary payload into a PublicationEntry."""
        if not isinstance(data, dict):
            raise ModelFormatError("PublicationEntry payload must be a dictionary.")
        line_num = data.get("line_number")
        subj = data.get("subject_name_verbatim")
        if line_num is None or subj is None:
            raise ModelFormatError(
                "PublicationEntry requires 'line_number' and 'subject_name_verbatim'."
            )
        return cls.create(
            line_number=int(line_num),
            subject_name_verbatim=str(subj),
            individual_id=data.get("individual_id"),
            role_or_class_raw=data.get("role_or_class_raw"),
            page_or_plate=data.get("page_or_plate"),
            remarks_raw=data.get("remarks_raw"),
        )

    def to_json(self) -> str:
        """Serialize PublicationEntry to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> PublicationEntry:
        """Deserialize a JSON string directly into a PublicationEntry."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse PublicationEntry JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"Line {self.line_number}: {self.subject_name_verbatim}"


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class PeriodicalArticleRecord(SourceRecord):
    """Archival record for a periodical article, yearbook page, or published county/family history."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.EDUCATION,
        description="High-level archival domain category (EDUCATION, NARRATIVE, NEWS, FRATERNAL, CHURCH, OTHER).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.YEARBOOK_PAGE,
        description="Specific documentary classification (YEARBOOK_PAGE, COMMENCEMENT_PROGRAM, CLASS_ROSTER, MEMOIR, MISC, PHOTO).",
    )
    publication_title_raw: str = Field(
        ...,
        description="Verbatim title of the periodical, yearbook, journal, or county/family history.",
    )
    date_published: EventDate = Field(
        ...,
        description="Publication year or exact date of the issue or edition.",
    )
    publication_kind: str = Field(
        default="PERIODICAL",
        description="Functional publication genre (e.g., PERIODICAL, YEARBOOK, COUNTY_HISTORY, BIOGRAPHICAL_SKETCH).",
    )
    parent_source_id: SourceID | None = Field(
        default=None,
        description="Optional foreign key linking to a master Publication.source_id container.",
    )
    pub_code: str | None = Field(
        default=None,
        description="Optional uppercase publication code matching PUB_CODE_PATTERN.",
    )
    institution_or_publisher_raw: str | None = Field(
        default=None,
        description="Verbatim school, university, society, or publishing house name.",
    )
    institution_org_id: OrganizationID | None = Field(
        default=None,
        description="Resolved canonical OrganizationID of the issuing school or society.",
    )
    author_or_editor_raw: str | None = Field(
        default=None,
        description="Verbatim author, compiler, or editor name.",
    )
    article_or_chapter_title: str | None = Field(
        default=None,
        description="Verbatim article heading, chapter title, or yearbook section.",
    )
    volume_issue: str | None = Field(
        default=None,
        description="Verbatim volume, issue, or edition designation.",
    )
    page_or_plate: str | None = Field(
        default=None,
        description="Verbatim page number, range, or portrait plate designation.",
    )
    education_level: EducationLevel | None = Field(
        default=None,
        description="Standardized educational attainment level for academic publications.",
    )
    entries: tuple[PublicationEntry, ...] = Field(
        default=(),
        description="Optional ordered tuple of enumerated subjects on a yearbook or directory page.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _PERIODICAL_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _PERIODICAL_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, title, pub_code, and unique line numbers."""
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

        clean_title = self.publication_title_raw.strip()
        if not clean_title:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'publication_title_raw' cannot be empty or whitespace."
            )
        if clean_title != self.publication_title_raw:
            object.__setattr__(self, "publication_title_raw", clean_title)

        clean_kind = self.publication_kind.strip().upper()
        if not clean_kind:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'publication_kind' cannot be empty or whitespace."
            )
        if clean_kind != self.publication_kind:
            object.__setattr__(self, "publication_kind", clean_kind)

        if self.pub_code is not None:
            clean_code = self.pub_code.strip().upper()
            if not PUB_CODE_REGEX.match(clean_code):
                raise ModelFormatError(
                    f"Invalid pub_code format: '{self.pub_code}'. "
                    "Must match '^[A-Z0-9_-]{2,20}$'."
                )
            if clean_code != self.pub_code:
                object.__setattr__(self, "pub_code", clean_code)

        seen_lines: set[int] = set()
        for entry in self.entries:
            if entry.line_number in seen_lines:
                raise ModelFormatError(
                    f"Duplicate PublicationEntry line_number {entry.line_number} within record."
                )
            seen_lines.add(entry.line_number)

    @property
    def entry_count(self) -> int:
        """Return the count of enumerated subject entries on this page."""
        return len(self.entries)

    def flatten_entries(self) -> tuple[dict[str, Any], ...]:
        """Flatten publication header context with each enumerated entry for tabular indexing."""
        header: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "publication_title_raw": self.publication_title_raw,
            "date_published": str(self.date_published),
            "publication_kind": self.publication_kind,
            "parent_source_id": str(self.parent_source_id) if self.parent_source_id else None,
            "pub_code": self.pub_code,
            "institution_or_publisher_raw": self.institution_or_publisher_raw,
            "institution_org_id": (
                str(self.institution_org_id) if self.institution_org_id else None
            ),
            "article_or_chapter_title": self.article_or_chapter_title,
            "volume_issue": self.volume_issue,
        }
        return tuple({**header, **entry.to_dict()} for entry in self.entries)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        publication_title_raw: str,
        date_published: EventDate | dict[str, Any] | str,
        publication_kind: str = "PERIODICAL",
        record_category: SourceRecordCategory | str = SourceRecordCategory.EDUCATION,
        record_type: SourceRecordType | str = SourceRecordType.YEARBOOK_PAGE,
        parent_source_id: SourceID | str | None = None,
        pub_code: str | None = None,
        institution_or_publisher_raw: str | None = None,
        institution_org_id: OrganizationID | str | None = None,
        author_or_editor_raw: str | None = None,
        article_or_chapter_title: str | None = None,
        volume_issue: str | None = None,
        page_or_plate: str | None = None,
        education_level: EducationLevel | str | None = None,
        entries: list[PublicationEntry | dict[str, Any]]
        | tuple[PublicationEntry, ...]
        | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> PeriodicalArticleRecord:
        """Factory constructor instantiating a validated PeriodicalArticleRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = (
            source_urn if isinstance(source_urn, ArchivalURN) else SourceURN(str(source_urn))
        )
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        res_cat = coerce_enum(SourceRecordCategory, record_category, field_name="record_category")
        res_type = coerce_enum(SourceRecordType, record_type, field_name="record_type")
        res_parent = (
            parent_source_id
            if (parent_source_id is None or isinstance(parent_source_id, SourceID))
            else SourceID(parent_source_id)
        )
        res_org = (
            institution_org_id
            if (institution_org_id is None or isinstance(institution_org_id, OrganizationID))
            else OrganizationID(institution_org_id)
        )
        res_edu = (
            coerce_enum(EducationLevel, education_level, field_name="education_level")
            if education_level is not None
            else None
        )
        res_date = _deserialize_event_date(date_published, "date_published")

        resolved_entries: tuple[PublicationEntry, ...] = tuple(
            e if isinstance(e, PublicationEntry) else PublicationEntry.from_dict(e)
            for e in (entries or ())
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
            publication_title_raw=publication_title_raw,
            date_published=res_date,
            publication_kind=(
                publication_kind.strip().upper()
                if isinstance(publication_kind, str)
                else publication_kind
            ),
            parent_source_id=res_parent,
            pub_code=pub_code.strip().upper() if isinstance(pub_code, str) else pub_code,
            institution_or_publisher_raw=institution_or_publisher_raw,
            institution_org_id=res_org,
            author_or_editor_raw=author_or_editor_raw,
            article_or_chapter_title=article_or_chapter_title,
            volume_issue=volume_issue,
            page_or_plate=page_or_plate,
            education_level=res_edu,
            entries=resolved_entries,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize PeriodicalArticleRecord to a dictionary."""
        data = super().to_dict()
        data["entries"] = [e.to_dict() for e in self.entries]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PeriodicalArticleRecord:
        """Deserialize a dictionary payload into a PeriodicalArticleRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("PeriodicalArticleRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        title_raw = data.get("publication_title_raw")
        raw_date = data.get("date_published")

        if not all((sid, raw_urn, desc, rep, audit_payload, title_raw, raw_date)):
            raise ModelFormatError(
                "PeriodicalArticleRecord requires source_id, source_urn, description, "
                "repository_id, audit, publication_title_raw, and date_published."
            )

        if not isinstance(audit_payload, (AuditStamp, dict)):
            raise ModelFormatError(
                "PeriodicalArticleRecord audit must be an AuditStamp or dictionary."
            )
        audit_obj = AuditStamp.from_dict(audit_payload)

        tombstone_payload = data.get("tombstone")
        tombstone_obj = (
            Tombstone.from_dict(tombstone_payload, id_cls=SourceID)
            if isinstance(tombstone_payload, dict)
            else None
        )

        raw_entries = data.get("entries", [])
        if not isinstance(raw_entries, (list, tuple)):
            raise ModelFormatError("PeriodicalArticleRecord 'entries' must be a list or tuple.")

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            publication_title_raw=str(title_raw),
            date_published=cast(Any, raw_date),
            publication_kind=str(data.get("publication_kind", "PERIODICAL")),
            record_category=data.get("record_category", SourceRecordCategory.EDUCATION),
            record_type=data.get("record_type", SourceRecordType.YEARBOOK_PAGE),
            parent_source_id=data.get("parent_source_id"),
            pub_code=data.get("pub_code"),
            institution_or_publisher_raw=data.get("institution_or_publisher_raw"),
            institution_org_id=data.get("institution_org_id"),
            author_or_editor_raw=data.get("author_or_editor_raw"),
            article_or_chapter_title=data.get("article_or_chapter_title"),
            volume_issue=data.get("volume_issue"),
            page_or_plate=data.get("page_or_plate"),
            education_level=data.get("education_level"),
            entries=list(raw_entries),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"PeriodicalArticleRecord [{self.publication_title_raw}] ({self.date_published})"
