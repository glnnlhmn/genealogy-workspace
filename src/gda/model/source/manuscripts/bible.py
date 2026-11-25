"""Path: src/gda/model/source/manuscripts/bible.py

Family Bible vital registers and genealogical inscriptions.

Operational Role:
    Defines BibleRegisterEntry (individual birth, marriage, or death entry inscribed
    on a family Bible register page) and FamilyBibleRecord (extending SourceRecord)
    for collection-wide family Bible registers with flatten_entries() tabular
    projection.
"""

from __future__ import annotations

import json
import re
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums import coerce_enum
from gda.core.enums.core import FactType
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import URN_REGEXES
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.3"

__all__ = [
    "BibleRegisterEntry",
    "FamilyBibleRecord",
]

_BIBLE_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.MANUSCRIPT,
        SourceRecordCategory.VITAL,
        SourceRecordCategory.OTHER,
    }
)

_BIBLE_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.BIBLE,
        SourceRecordType.BIBLE_RECORD,
    }
)

_ALLOWED_ENTRY_EVENTS: frozenset[FactType] = frozenset(
    {
        FactType.BIRTH,
        FactType.BAPTISM,
        FactType.MARRIAGE,
        FactType.DEATH,
        FactType.BURIAL,
        FactType.OTHER,
    }
)

_MS_URN_PATTERN: re.Pattern[str] = URN_REGEXES["MS"]
_BIBLE_URN_PATTERN: re.Pattern[str] = URN_REGEXES["BIBLE"]


def _resolve_manuscript_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into ArchivalURN (URN:MS:... / URN:BIBLE:...) or SourceURN."""
    if isinstance(raw, ArchivalURN):
        return raw
    token = str(raw).strip()
    if token.startswith(("URN:MS:", "URN:BIBLE:")):
        if not (_MS_URN_PATTERN.match(token) or _BIBLE_URN_PATTERN.match(token)):
            raise ModelFormatError(
                f"Invalid Manuscript/Bible URN syntax: '{token}'. "
                "Must match 'URN:<MS|BIBLE>:<YEAR>:<JURISDICTION>:<LOCATOR>'."
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


def _parse_entry_fact_type(raw: FactType | str) -> FactType:
    """Resolve FactType for a family Bible register line."""
    try:
        resolved = coerce_enum(FactType, raw, field_name="event_type")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid FactType value: '{raw}'.") from err

    if resolved not in _ALLOWED_ENTRY_EVENTS:
        raise ModelFormatError(
            f"BibleRegisterEntry event_type must be in "
            f"{sorted(f.value for f in _ALLOWED_ENTRY_EVENTS)}, got '{resolved.value}'."
        )
    return resolved


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class BibleRegisterEntry(IntrospectableMixin):
    """Single vital event line inscribed on a family Bible register page."""

    line_number: int = Field(
        ...,
        ge=1,
        description="1-based line number on the Bible family record sheet.",
    )
    event_type: FactType = Field(
        default=FactType.BIRTH,
        description="Vital event classification (BIRTH, BAPTISM, MARRIAGE, DEATH, BURIAL, OTHER).",
    )
    subject_name_raw: str = Field(
        ...,
        description="Verbatim full name of the primary person named in the register line.",
    )
    subject_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the primary person if linked.",
    )
    secondary_name_raw: str | None = Field(
        default=None,
        description="Verbatim spouse name (for marriages) or parent names (for births/deaths).",
    )
    secondary_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the spouse or secondary person if linked.",
    )
    event_date: EventDate | None = Field(
        default=None,
        description="Inscribed date of the vital event.",
    )
    place_raw: str | None = Field(
        default=None,
        description="Verbatim place of birth, marriage, or death if recorded on the line.",
    )
    place_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the event place.",
    )
    transcription_raw: str | None = Field(
        default=None,
        description="Exact diplomatic transcription of the register line.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty subject_name_raw and allowed FactType."""
        clean_subj = self.subject_name_raw.strip()
        if not clean_subj:
            raise ModelFormatError(
                "BibleRegisterEntry 'subject_name_raw' cannot be empty or whitespace.",
                details={"line_number": self.line_number},
            )
        if clean_subj != self.subject_name_raw:
            object.__setattr__(self, "subject_name_raw", clean_subj)

        if self.event_type not in _ALLOWED_ENTRY_EVENTS:
            raise ModelFormatError(
                f"BibleRegisterEntry event_type must be in "
                f"{sorted(f.value for f in _ALLOWED_ENTRY_EVENTS)}, got '{self.event_type.value}'."
            )

    @classmethod
    def create(
        cls,
        line_number: int,
        subject_name_raw: str,
        event_type: FactType | str = FactType.BIRTH,
        subject_id: IndividualID | str | None = None,
        secondary_name_raw: str | None = None,
        secondary_id: IndividualID | str | None = None,
        event_date: EventDate | dict[str, Any] | str | None = None,
        place_raw: str | None = None,
        place_id: LocationID | str | None = None,
        transcription_raw: str | None = None,
    ) -> BibleRegisterEntry:
        """Factory constructor instantiating a validated BibleRegisterEntry."""
        res_subj = (
            subject_id
            if (subject_id is None or isinstance(subject_id, IndividualID))
            else IndividualID(subject_id)
        )
        res_sec = (
            secondary_id
            if (secondary_id is None or isinstance(secondary_id, IndividualID))
            else IndividualID(secondary_id)
        )
        res_dt = (
            _deserialize_event_date(event_date, "event_date") if event_date is not None else None
        )
        res_loc = (
            place_id
            if (place_id is None or isinstance(place_id, LocationID))
            else LocationID(place_id)
        )
        return cls(
            line_number=line_number,
            event_type=_parse_entry_fact_type(event_type),
            subject_name_raw=subject_name_raw,
            subject_id=res_subj,
            secondary_name_raw=secondary_name_raw,
            secondary_id=res_sec,
            event_date=res_dt,
            place_raw=place_raw,
            place_id=res_loc,
            transcription_raw=transcription_raw,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize BibleRegisterEntry to a dictionary."""
        data: dict[str, Any] = {
            "line_number": self.line_number,
            "event_type": self.event_type.value,
            "subject_name_raw": self.subject_name_raw,
        }
        if self.subject_id is not None:
            data["subject_id"] = str(self.subject_id)
        if self.secondary_name_raw is not None:
            data["secondary_name_raw"] = self.secondary_name_raw
        if self.secondary_id is not None:
            data["secondary_id"] = str(self.secondary_id)
        if self.event_date is not None:
            data["event_date"] = self.event_date.to_dict()
        if self.place_raw is not None:
            data["place_raw"] = self.place_raw
        if self.place_id is not None:
            data["place_id"] = str(self.place_id)
        if self.transcription_raw is not None:
            data["transcription_raw"] = self.transcription_raw
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BibleRegisterEntry:
        """Deserialize a dictionary payload into a BibleRegisterEntry."""
        if not isinstance(data, dict):
            raise ModelFormatError("BibleRegisterEntry payload must be a dictionary.")
        line_num = data.get("line_number")
        subj = data.get("subject_name_raw")
        if line_num is None or subj is None:
            raise ModelFormatError(
                "BibleRegisterEntry requires 'line_number' and 'subject_name_raw'."
            )
        return cls.create(
            line_number=int(line_num),
            subject_name_raw=str(subj),
            event_type=data.get("event_type", FactType.BIRTH),
            subject_id=data.get("subject_id"),
            secondary_name_raw=data.get("secondary_name_raw"),
            secondary_id=data.get("secondary_id"),
            event_date=data.get("event_date"),
            place_raw=data.get("place_raw"),
            place_id=data.get("place_id"),
            transcription_raw=data.get("transcription_raw"),
        )

    def to_json(self) -> str:
        """Serialize BibleRegisterEntry to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> BibleRegisterEntry:
        """Deserialize a JSON string directly into a BibleRegisterEntry."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse BibleRegisterEntry JSON string: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"Line {self.line_number} [{self.event_type.value}]: {self.subject_name_raw}"


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class FamilyBibleRecord(SourceRecord):
    """Primary archival record documenting a family Bible vital register and provenance."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.MANUSCRIPT,
        description="High-level archival domain category (MANUSCRIPT, VITAL, OTHER).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.BIBLE_RECORD,
        description="Specific record type (BIBLE or BIBLE_RECORD).",
    )
    family_surname: str = Field(
        ...,
        description="Primary family surname associated with the Bible register.",
    )
    edition_imprint: str | None = Field(
        default=None,
        description="Publisher, city, and title-page imprint details of the Bible edition.",
    )
    publication_year: int | None = Field(
        default=None,
        ge=1450,
        le=2100,
        description="Title-page publication year establishing terminus post quem for contemporary entries.",
    )
    original_owner_raw: str | None = Field(
        default=None,
        description="Verbatim name of the original owner inscribed on the flyleaf.",
    )
    original_owner_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the original owner.",
    )
    custodian_or_provenance: str | None = Field(
        default=None,
        description="Chain of custody, present holder, or archival deposit provenance.",
    )
    entries: tuple[BibleRegisterEntry, ...] = Field(
        default=(),
        description="Ordered tuple of vital event entries inscribed in the Bible register.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _BIBLE_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _BIBLE_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, non-empty family_surname, and unique line numbers."""
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

        clean_surname = self.family_surname.strip()
        if not clean_surname:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'family_surname' cannot be empty or whitespace."
            )
        if clean_surname != self.family_surname:
            object.__setattr__(self, "family_surname", clean_surname)

        seen_lines: set[int] = set()
        for entry in self.entries:
            if entry.line_number in seen_lines:
                raise ModelFormatError(
                    f"Duplicate BibleRegisterEntry line_number {entry.line_number} within record."
                )
            seen_lines.add(entry.line_number)

    @property
    def entry_count(self) -> int:
        """Return count of vital register entries recorded in this Bible."""
        return len(self.entries)

    def flatten_entries(self) -> tuple[dict[str, Any], ...]:
        """Flatten family Bible provenance header with each vital register entry."""
        header: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "family_surname": self.family_surname,
            "publication_year": self.publication_year,
        }
        return tuple({**header, **entry.to_dict()} for entry in self.entries)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        family_surname: str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.MANUSCRIPT,
        record_type: SourceRecordType | str = SourceRecordType.BIBLE_RECORD,
        edition_imprint: str | None = None,
        publication_year: int | None = None,
        original_owner_raw: str | None = None,
        original_owner_id: IndividualID | str | None = None,
        custodian_or_provenance: str | None = None,
        entries: list[BibleRegisterEntry | dict[str, Any]]
        | tuple[BibleRegisterEntry, ...]
        | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> FamilyBibleRecord:
        """Factory constructor instantiating a validated FamilyBibleRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_manuscript_urn(source_urn)
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        res_cat = coerce_enum(SourceRecordCategory, record_category, field_name="record_category")
        res_type = coerce_enum(SourceRecordType, record_type, field_name="record_type")
        res_owner_id = (
            original_owner_id
            if (original_owner_id is None or isinstance(original_owner_id, IndividualID))
            else IndividualID(original_owner_id)
        )
        resolved_entries: tuple[BibleRegisterEntry, ...] = tuple(
            e if isinstance(e, BibleRegisterEntry) else BibleRegisterEntry.from_dict(e)
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
            family_surname=family_surname,
            edition_imprint=edition_imprint,
            publication_year=publication_year,
            original_owner_raw=original_owner_raw,
            original_owner_id=res_owner_id,
            custodian_or_provenance=custodian_or_provenance,
            entries=resolved_entries,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize FamilyBibleRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "family_surname": self.family_surname,
                "entries": [e.to_dict() for e in self.entries],
            }
        )
        if self.edition_imprint is not None:
            data["edition_imprint"] = self.edition_imprint
        if self.publication_year is not None:
            data["publication_year"] = self.publication_year
        if self.original_owner_raw is not None:
            data["original_owner_raw"] = self.original_owner_raw
        if self.original_owner_id is not None:
            data["original_owner_id"] = str(self.original_owner_id)
        if self.custodian_or_provenance is not None:
            data["custodian_or_provenance"] = self.custodian_or_provenance
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FamilyBibleRecord:
        """Deserialize a dictionary payload into a FamilyBibleRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("FamilyBibleRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        surname = data.get("family_surname")

        if not all((sid, raw_urn, desc, rep, audit_payload, surname)):
            raise ModelFormatError(
                "FamilyBibleRecord requires source_id, source_urn, description, repository_id, "
                "audit, and family_surname."
            )

        if not isinstance(audit_payload, (AuditStamp, dict)):
            raise ModelFormatError("FamilyBibleRecord audit must be an AuditStamp or dictionary.")
        audit_obj = AuditStamp.from_dict(audit_payload)

        tombstone_payload = data.get("tombstone")
        tombstone_obj = (
            Tombstone.from_dict(tombstone_payload, id_cls=SourceID)
            if isinstance(tombstone_payload, dict)
            else None
        )

        raw_entries = data.get("entries", [])
        if not isinstance(raw_entries, (list, tuple)):
            raise ModelFormatError("FamilyBibleRecord 'entries' must be a list or tuple.")

        raw_pub_year = data.get("publication_year")
        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            family_surname=str(surname),
            record_category=data.get("record_category", SourceRecordCategory.MANUSCRIPT),
            record_type=data.get("record_type", SourceRecordType.BIBLE_RECORD),
            edition_imprint=data.get("edition_imprint"),
            publication_year=int(raw_pub_year) if raw_pub_year is not None else None,
            original_owner_raw=data.get("original_owner_raw"),
            original_owner_id=data.get("original_owner_id"),
            custodian_or_provenance=data.get("custodian_or_provenance"),
            entries=list(raw_entries),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"FamilyBibleRecord [{self.family_surname}] ({self.entry_count} entries)"
