"""Path: src/gda/model/publications/newspaper.py

Newspaper article, obituary, vital notice, and clipping domain models.

Operational Role:
    Defines NewspaperClipRecord extending SourceRecord to capture single-row
    evidentiary newspaper items (obituaries, marriage/birth/death notices, local
    news columns, society items, and legal notices), optionally linked to a
    parent Publication source container via parent_source_id and pub_code.
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.types import NEWS_CATEGORY_REGEX, PUB_CODE_REGEX
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.1"

__all__ = [
    "NewspaperClipRecord",
]

_NEWSPAPER_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.NEWS,
        SourceRecordCategory.VITAL,
        SourceRecordCategory.LEGAL,
        SourceRecordCategory.OTHER,
    }
)

_NEWSPAPER_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.MISC,
        SourceRecordType.AFFIDAVIT,
        SourceRecordType.DOCKET_ENTRY,
        SourceRecordType.DEATH_CERTIFICATE,
        SourceRecordType.MARRIAGE_LICENSE,
        SourceRecordType.BIRTH_CERTIFICATE,
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
class NewspaperClipRecord(SourceRecord):
    """Single-row archival record representing a newspaper article, obituary, or notice."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.NEWS,
        description="High-level archival domain category (NEWS, VITAL, LEGAL, OTHER).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.MISC,
        description="Specific documentary classification for the newspaper clipping.",
    )
    newspaper_name_raw: str = Field(
        ...,
        description="Verbatim newspaper masthead title printed on the issue.",
    )
    issue_date: EventDate = Field(
        ...,
        description="Publication date of the newspaper issue.",
    )
    news_category: str = Field(
        default="GENERAL",
        description="Uppercase editorial classification matching NEWS_CATEGORY_PATTERN (e.g., OBITUARY, MARRIAGE).",
    )
    parent_source_id: SourceID | None = Field(
        default=None,
        description="Optional foreign key linking to a master Publication.source_id container.",
    )
    pub_code: str | None = Field(
        default=None,
        description="Optional uppercase publication code matching PUB_CODE_PATTERN.",
    )
    publication_location_raw: str | None = Field(
        default=None,
        description="Verbatim city and state of publication printed on the masthead.",
    )
    publication_location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the place of publication.",
    )
    headline_raw: str | None = Field(
        default=None,
        description="Verbatim headline or column heading of the clipping.",
    )
    byline_raw: str | None = Field(
        default=None,
        description="Verbatim correspondent, reporter, or contributor byline.",
    )
    volume_issue: str | None = Field(
        default=None,
        description="Verbatim volume and issue numbering (e.g., 'Vol. XLII, No. 14').",
    )
    page_column: str | None = Field(
        default=None,
        description="Verbatim page and column locator (e.g., 'p. 4, col. 2').",
    )
    edition: str | None = Field(
        default=None,
        description="Edition designation if printed (e.g., 'Morning Edition', 'Weekly').",
    )
    article_summary: str | None = Field(
        default=None,
        description="Concise genealogical abstract of the clipping's assertions.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _NEWSPAPER_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _NEWSPAPER_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, masthead, news_category, and pub_code bounds."""
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

        clean_paper = self.newspaper_name_raw.strip()
        if not clean_paper:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'newspaper_name_raw' cannot be empty or whitespace."
            )
        if clean_paper != self.newspaper_name_raw:
            object.__setattr__(self, "newspaper_name_raw", clean_paper)

        clean_news_cat = self.news_category.strip().upper()
        if not NEWS_CATEGORY_REGEX.match(clean_news_cat):
            raise ModelFormatError(
                f"Invalid news_category format: '{self.news_category}'. "
                "Must match '^[A-Z]{3,15}$'."
            )
        if clean_news_cat != self.news_category:
            object.__setattr__(self, "news_category", clean_news_cat)

        if self.pub_code is not None:
            clean_code = self.pub_code.strip().upper()
            if not PUB_CODE_REGEX.match(clean_code):
                raise ModelFormatError(
                    f"Invalid pub_code format: '{self.pub_code}'. "
                    "Must match '^[A-Z0-9_-]{2,20}$'."
                )
            if clean_code != self.pub_code:
                object.__setattr__(self, "pub_code", clean_code)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        newspaper_name_raw: str,
        issue_date: EventDate | dict[str, Any] | str,
        news_category: str = "GENERAL",
        record_category: SourceRecordCategory | str = SourceRecordCategory.NEWS,
        record_type: SourceRecordType | str = SourceRecordType.MISC,
        parent_source_id: SourceID | str | None = None,
        pub_code: str | None = None,
        publication_location_raw: str | None = None,
        publication_location_id: LocationID | str | None = None,
        headline_raw: str | None = None,
        byline_raw: str | None = None,
        volume_issue: str | None = None,
        page_column: str | None = None,
        edition: str | None = None,
        article_summary: str | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> NewspaperClipRecord:
        """Factory constructor instantiating a validated NewspaperClipRecord."""
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
        res_parent = (
            parent_source_id
            if (parent_source_id is None or isinstance(parent_source_id, SourceID))
            else SourceID(parent_source_id)
        )
        res_loc = (
            publication_location_id
            if (publication_location_id is None or isinstance(publication_location_id, LocationID))
            else LocationID(publication_location_id)
        )
        res_issue_date = _deserialize_event_date(issue_date, "issue_date")
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
            newspaper_name_raw=newspaper_name_raw,
            issue_date=res_issue_date,
            news_category=(
                news_category.strip().upper() if isinstance(news_category, str) else news_category
            ),
            parent_source_id=res_parent,
            pub_code=pub_code.strip().upper() if isinstance(pub_code, str) else pub_code,
            publication_location_raw=publication_location_raw,
            publication_location_id=res_loc,
            headline_raw=headline_raw,
            byline_raw=byline_raw,
            volume_issue=volume_issue,
            page_column=page_column,
            edition=edition,
            article_summary=article_summary,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize NewspaperClipRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "newspaper_name_raw": self.newspaper_name_raw,
                "issue_date": self.issue_date.to_dict(),
                "news_category": self.news_category,
            }
        )
        if self.parent_source_id is not None:
            data["parent_source_id"] = str(self.parent_source_id)
        if self.pub_code is not None:
            data["pub_code"] = self.pub_code
        if self.publication_location_raw is not None:
            data["publication_location_raw"] = self.publication_location_raw
        if self.publication_location_id is not None:
            data["publication_location_id"] = str(self.publication_location_id)
        if self.headline_raw is not None:
            data["headline_raw"] = self.headline_raw
        if self.byline_raw is not None:
            data["byline_raw"] = self.byline_raw
        if self.volume_issue is not None:
            data["volume_issue"] = self.volume_issue
        if self.page_column is not None:
            data["page_column"] = self.page_column
        if self.edition is not None:
            data["edition"] = self.edition
        if self.article_summary is not None:
            data["article_summary"] = self.article_summary
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NewspaperClipRecord:
        """Deserialize a dictionary payload into a NewspaperClipRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("NewspaperClipRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        paper_name = data.get("newspaper_name_raw")
        raw_issue_date = data.get("issue_date")

        if not all((sid, raw_urn, desc, rep, audit_payload, paper_name, raw_issue_date)):
            raise ModelFormatError(
                "NewspaperClipRecord requires source_id, source_urn, description, repository_id, "
                "audit, newspaper_name_raw, and issue_date."
            )

        if isinstance(audit_payload, AuditStamp):
            audit_obj = audit_payload
        elif isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )
        else:
            raise ModelFormatError("NewspaperClipRecord audit must be an AuditStamp or dictionary.")

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
            newspaper_name_raw=str(paper_name),
            issue_date=raw_issue_date,
            news_category=str(data.get("news_category", "GENERAL")),
            record_category=data.get("record_category", SourceRecordCategory.NEWS),
            record_type=data.get("record_type", SourceRecordType.MISC),
            parent_source_id=data.get("parent_source_id"),
            pub_code=data.get("pub_code"),
            publication_location_raw=data.get("publication_location_raw"),
            publication_location_id=data.get("publication_location_id"),
            headline_raw=data.get("headline_raw"),
            byline_raw=data.get("byline_raw"),
            volume_issue=data.get("volume_issue"),
            page_column=data.get("page_column"),
            edition=data.get("edition"),
            article_summary=data.get("article_summary"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"NewspaperClipRecord [{self.newspaper_name_raw} - {self.news_category}] ({self.issue_date})"
