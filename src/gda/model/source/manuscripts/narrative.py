"""Path: src/gda/model/source/manuscripts/narrative.py

Manuscript collections, personal correspondence, diaries, memoirs, depositions, and oral histories.

Operational Role:
    Defines NarrativeManuscriptRecord (extending SourceRecord) to capture primary
    and secondary documentary evidence from personal letters, correspondence,
    diaries, memoirs, affidavits, depositions, oral histories, and interview
    transcripts.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.types import URN_REGEXES
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
    "NarrativeManuscriptRecord",
]

_MANUSCRIPT_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.MANUSCRIPT,
        SourceRecordCategory.NARRATIVE,
        SourceRecordCategory.LEGAL,
        SourceRecordCategory.OTHER,
    }
)

_MANUSCRIPT_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.AFFIDAVIT,
        SourceRecordType.DEPOSITION,
        SourceRecordType.MEMOIR,
        SourceRecordType.ORAL_HISTORY,
        SourceRecordType.INTERVIEW_TRANSCRIPT,
        SourceRecordType.PERSONAL_LETTER,
        SourceRecordType.DIARY,
        SourceRecordType.CORRESP,
    }
)

_MS_URN_PATTERN: re.Pattern[str] = URN_REGEXES["MS"]
_NARRATIVE_URN_PATTERN: re.Pattern[str] = URN_REGEXES["NARRATIVE"]


def _resolve_narrative_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into ArchivalURN (URN:MS:... / URN:NARRATIVE:...) or SourceURN."""
    if isinstance(raw, ArchivalURN):
        return raw
    token = str(raw).strip()
    if token.startswith(("URN:MS:", "URN:NARRATIVE:")):
        if not (_MS_URN_PATTERN.match(token) or _NARRATIVE_URN_PATTERN.match(token)):
            raise ModelFormatError(
                f"Invalid Manuscript/Narrative URN syntax: '{token}'. "
                "Must match 'URN:<MS|NARRATIVE>:<YEAR>:<JURISDICTION>:<LOCATOR>'."
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


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class NarrativeManuscriptRecord(SourceRecord):
    """Primary or secondary record documenting correspondence, diaries, memoirs, or depositions."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.MANUSCRIPT,
        description="High-level archival domain category (MANUSCRIPT, NARRATIVE, LEGAL, OTHER).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.PERSONAL_LETTER,
        description="Specific manuscript or narrative instrument classification.",
    )
    title_or_subject: str = Field(
        ...,
        description="Title of the manuscript, memoir, diary, or subject line of correspondence.",
    )
    author_or_sender_raw: str | None = Field(
        default=None,
        description="Verbatim name of the author, diarist, letter writer, deponent, or interviewee.",
    )
    author_or_sender_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the author or sender.",
    )
    recipient_raw: str | None = Field(
        default=None,
        description="Verbatim name of the letter recipient or interviewer.",
    )
    recipient_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the recipient.",
    )
    collection_name: str | None = Field(
        default=None,
        description="Archival manuscript collection or series name.",
    )
    box_folder_or_page: str | None = Field(
        default=None,
        description="Box, folder, volume, or page locator within the manuscript or book.",
    )
    origin_place_raw: str | None = Field(
        default=None,
        description="Verbatim dateline place of writing or publication.",
    )
    origin_place_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the place of writing.",
    )
    destination_place_raw: str | None = Field(
        default=None,
        description="Verbatim postal destination or addressee location.",
    )
    destination_place_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the postal destination.",
    )
    date_written_or_published: EventDate | None = Field(
        default=None,
        description="Date the letter, diary entry, or narrative was written or published.",
    )
    transcript_excerpt: str | None = Field(
        default=None,
        description="Diplomatic transcription or key genealogical excerpt from the text.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _MANUSCRIPT_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _MANUSCRIPT_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, and non-empty title_or_subject hygiene."""
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

        clean_title = self.title_or_subject.strip()
        if not clean_title:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'title_or_subject' cannot be empty or whitespace."
            )
        if clean_title != self.title_or_subject:
            object.__setattr__(self, "title_or_subject", clean_title)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        title_or_subject: str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.MANUSCRIPT,
        record_type: SourceRecordType | str = SourceRecordType.PERSONAL_LETTER,
        author_or_sender_raw: str | None = None,
        author_or_sender_id: IndividualID | str | None = None,
        recipient_raw: str | None = None,
        recipient_id: IndividualID | str | None = None,
        collection_name: str | None = None,
        box_folder_or_page: str | None = None,
        origin_place_raw: str | None = None,
        origin_place_id: LocationID | str | None = None,
        destination_place_raw: str | None = None,
        destination_place_id: LocationID | str | None = None,
        date_written_or_published: EventDate | dict[str, Any] | str | None = None,
        transcript_excerpt: str | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> NarrativeManuscriptRecord:
        """Factory constructor instantiating a validated NarrativeManuscriptRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_narrative_urn(source_urn)
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
        res_author_id = (
            author_or_sender_id
            if (author_or_sender_id is None or isinstance(author_or_sender_id, IndividualID))
            else IndividualID(author_or_sender_id)
        )
        res_recip_id = (
            recipient_id
            if (recipient_id is None or isinstance(recipient_id, IndividualID))
            else IndividualID(recipient_id)
        )
        res_orig_loc = (
            origin_place_id
            if (origin_place_id is None or isinstance(origin_place_id, LocationID))
            else LocationID(origin_place_id)
        )
        res_dest_loc = (
            destination_place_id
            if (destination_place_id is None or isinstance(destination_place_id, LocationID))
            else LocationID(destination_place_id)
        )
        res_date = (
            _deserialize_event_date(date_written_or_published, "date_written_or_published")
            if date_written_or_published is not None
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
            title_or_subject=title_or_subject,
            author_or_sender_raw=author_or_sender_raw,
            author_or_sender_id=res_author_id,
            recipient_raw=recipient_raw,
            recipient_id=res_recip_id,
            collection_name=collection_name,
            box_folder_or_page=box_folder_or_page,
            origin_place_raw=origin_place_raw,
            origin_place_id=res_orig_loc,
            destination_place_raw=destination_place_raw,
            destination_place_id=res_dest_loc,
            date_written_or_published=res_date,
            transcript_excerpt=transcript_excerpt,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize NarrativeManuscriptRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "title_or_subject": self.title_or_subject,
            }
        )
        if self.author_or_sender_raw is not None:
            data["author_or_sender_raw"] = self.author_or_sender_raw
        if self.author_or_sender_id is not None:
            data["author_or_sender_id"] = str(self.author_or_sender_id)
        if self.recipient_raw is not None:
            data["recipient_raw"] = self.recipient_raw
        if self.recipient_id is not None:
            data["recipient_id"] = str(self.recipient_id)
        if self.collection_name is not None:
            data["collection_name"] = self.collection_name
        if self.box_folder_or_page is not None:
            data["box_folder_or_page"] = self.box_folder_or_page
        if self.origin_place_raw is not None:
            data["origin_place_raw"] = self.origin_place_raw
        if self.origin_place_id is not None:
            data["origin_place_id"] = str(self.origin_place_id)
        if self.destination_place_raw is not None:
            data["destination_place_raw"] = self.destination_place_raw
        if self.destination_place_id is not None:
            data["destination_place_id"] = str(self.destination_place_id)
        if self.date_written_or_published is not None:
            data["date_written_or_published"] = self.date_written_or_published.to_dict()
        if self.transcript_excerpt is not None:
            data["transcript_excerpt"] = self.transcript_excerpt
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NarrativeManuscriptRecord:
        """Deserialize a dictionary payload into a NarrativeManuscriptRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("NarrativeManuscriptRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        title = data.get("title_or_subject")

        if not all((sid, raw_urn, desc, rep, audit_payload, title)):
            raise ModelFormatError(
                "NarrativeManuscriptRecord requires source_id, source_urn, description, "
                "repository_id, audit, and title_or_subject."
            )

        if isinstance(audit_payload, AuditStamp):
            audit_obj = audit_payload
        elif isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )
        else:
            raise ModelFormatError(
                "NarrativeManuscriptRecord audit must be an AuditStamp or dictionary."
            )

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
            title_or_subject=str(title),
            record_category=data.get("record_category", SourceRecordCategory.MANUSCRIPT),
            record_type=data.get("record_type", SourceRecordType.PERSONAL_LETTER),
            author_or_sender_raw=data.get("author_or_sender_raw"),
            author_or_sender_id=data.get("author_or_sender_id"),
            recipient_raw=data.get("recipient_raw"),
            recipient_id=data.get("recipient_id"),
            collection_name=data.get("collection_name"),
            box_folder_or_page=data.get("box_folder_or_page"),
            origin_place_raw=data.get("origin_place_raw"),
            origin_place_id=data.get("origin_place_id"),
            destination_place_raw=data.get("destination_place_raw"),
            destination_place_id=data.get("destination_place_id"),
            date_written_or_published=data.get("date_written_or_published"),
            transcript_excerpt=data.get("transcript_excerpt"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"NarrativeManuscriptRecord [{self.record_type.value}] {self.title_or_subject}"
