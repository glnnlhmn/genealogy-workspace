"""Path: src/gda/model/source/publications/publication.py

Master serial, newspaper, periodical, and monograph publication source container models.

Operational Role:
    Defines Publication extending SourceRecord to represent a newspaper run,
    periodical title, journal, yearbook series, or published county/family
    history as a canonical top-level source container (keyed by SourceID and
    PUB_CODE_REGEX), supporting multi-phase historical masthead/title changes
    via NameThing and temporal publication bounds via TimePeriod.
"""

from __future__ import annotations

from typing import Any, ClassVar, cast

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums import coerce_enum
from gda.core.enums.archival import PublicationFrequency
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.types import PUB_CODE_REGEX
from gda.model.atom.id import LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.3"

__all__ = [
    "Publication",
]

_PUBLICATION_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.NEWS,
        SourceRecordCategory.EDUCATION,
        SourceRecordCategory.DIRECTORY,
        SourceRecordCategory.NARRATIVE,
        SourceRecordCategory.OTHER,
    }
)


def _parse_frequency(raw: PublicationFrequency | str) -> PublicationFrequency:
    """Resolve PublicationFrequency from enum member, value string, or member name."""
    try:
        return coerce_enum(PublicationFrequency, raw, field_name="frequency")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid PublicationFrequency value: '{raw}'.") from err


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class Publication(SourceRecord):
    """Canonical top-level source container representing a serial or monograph publication."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.NEWS,
        description="High-level archival domain category (NEWS, EDUCATION, DIRECTORY, NARRATIVE, OTHER).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.MISC,
        description="Specific documentary record classification for the publication run.",
    )
    title: NameThing = Field(
        ...,
        description="Standardized naming value object capturing canonical and historic mastheads.",
    )
    pub_code: str = Field(
        ...,
        description="Short uppercase publication identifier matching PUB_CODE_PATTERN.",
    )
    frequency: PublicationFrequency | None = Field(
        default=None,
        description="Serial publication schedule classification (Daily, Weekly, Semi-Weekly, Monthly).",
    )
    publisher_raw: str | None = Field(
        default=None,
        description="Verbatim publisher, printer, or issuing institution name.",
    )
    place_of_publication_raw: str | None = Field(
        default=None,
        description="Verbatim city/state of publication.",
    )
    location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the place of publication.",
    )
    publication_period: TimePeriod | None = Field(
        default=None,
        description="Temporal bounds spanning inaugural issue/edition to cessation.",
    )
    issn_or_lccn: str | None = Field(
        default=None,
        description="Standardized ISSN, LCCN, or OCLC control number if cataloged.",
    )
    is_active: bool = Field(
        default=True,
        description="True if the serial publication is currently active or extant.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _PUBLICATION_CATEGORIES

    def __post_init__(self) -> None:
        """Enforce category bounds and canonical PUB_CODE_REGEX syntax."""
        super().__post_init__()

        if self.record_category not in self.ALLOWED_CATEGORIES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_category in "
                f"{sorted(c.value for c in self.ALLOWED_CATEGORIES)}, "
                f"got '{self.record_category.value}'."
            )

        clean_code = self.pub_code.strip().upper()
        if not PUB_CODE_REGEX.match(clean_code):
            raise ModelFormatError(
                f"Invalid pub_code format: '{self.pub_code}'. Must match '^[A-Z0-9_-]{{2,20}}$'."
            )
        if clean_code != self.pub_code:
            object.__setattr__(self, "pub_code", clean_code)

    @property
    def canonical_title(self) -> str:
        """Forward standardized canonical masthead or book title."""
        return self.title.canonical

    @property
    def aliases(self) -> list[str]:
        """Forward colloquial or abbreviated masthead aliases."""
        return self.title.aliases

    @property
    def historical_titles(self) -> list[HistoricVariant]:
        """Forward date-bounded masthead or title evolution phases."""
        return self.title.historic

    @property
    def first_issue_date(self) -> EventDate | None:
        """Convenience accessor for inaugural issue/edition date."""
        return self.publication_period.start_date if self.publication_period is not None else None

    @property
    def last_issue_date(self) -> EventDate | None:
        """Convenience accessor for final issue/edition date."""
        return self.publication_period.end_date if self.publication_period is not None else None

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        title: NameThing | str,
        pub_code: str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.NEWS,
        record_type: SourceRecordType | str = SourceRecordType.MISC,
        frequency: PublicationFrequency | str | None = None,
        publisher_raw: str | None = None,
        place_of_publication_raw: str | None = None,
        location_id: LocationID | str | None = None,
        publication_period: TimePeriod | None = None,
        issn_or_lccn: str | None = None,
        is_active: bool = True,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> Publication:
        """Factory constructor instantiating a validated Publication source container."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = (
            source_urn if isinstance(source_urn, ArchivalURN) else SourceURN(str(source_urn))
        )
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )

        if isinstance(title, NameThing):
            resolved_title = title
        elif isinstance(title, str):
            clean_title = title.strip()
            if not clean_title:
                raise ModelFormatError("Publication 'title' cannot be empty or whitespace.")
            resolved_title = NameThing.create(raw=clean_title, canonical=clean_title)
        else:
            raise TypeError(
                f"Publication 'title' must be NameThing or str, got {type(title).__name__}."
            )

        res_cat = coerce_enum(SourceRecordCategory, record_category, field_name="record_category")
        res_type = coerce_enum(SourceRecordType, record_type, field_name="record_type")
        res_freq = _parse_frequency(frequency) if frequency is not None else None
        res_loc = (
            location_id
            if (location_id is None or isinstance(location_id, LocationID))
            else LocationID(location_id)
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
            title=resolved_title,
            pub_code=pub_code.strip().upper() if isinstance(pub_code, str) else pub_code,
            frequency=res_freq,
            publisher_raw=publisher_raw,
            place_of_publication_raw=place_of_publication_raw,
            location_id=res_loc,
            publication_period=publication_period,
            issn_or_lccn=issn_or_lccn,
            is_active=is_active,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize Publication to a dictionary."""
        return super().to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Publication:
        """Deserialize a dictionary payload into a Publication."""
        if not isinstance(data, dict):
            raise ModelFormatError("Publication payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        raw_title = data.get("title")
        pub_code = data.get("pub_code")

        if not all((sid, raw_urn, desc, rep, audit_payload, raw_title, pub_code)):
            raise ModelFormatError(
                "Publication requires source_id, source_urn, description, repository_id, "
                "audit, title, and pub_code."
            )

        resolved_title: NameThing | str = (
            NameThing.from_dict(raw_title)
            if isinstance(raw_title, dict)
            else cast(NameThing | str, raw_title)
        )

        if not isinstance(audit_payload, (AuditStamp, dict)):
            raise ModelFormatError("Publication audit must be an AuditStamp or dictionary.")
        audit_obj = AuditStamp.from_dict(audit_payload)

        tombstone_payload = data.get("tombstone")
        tombstone_obj = (
            Tombstone.from_dict(tombstone_payload, id_cls=SourceID)
            if isinstance(tombstone_payload, dict)
            else None
        )

        raw_period = data.get("publication_period")
        resolved_period: TimePeriod | None = None
        if isinstance(raw_period, TimePeriod):
            resolved_period = raw_period
        elif isinstance(raw_period, dict) and (
            raw_period.get("start_date") is not None or raw_period.get("end_date") is not None
        ):
            resolved_period = TimePeriod.from_dict(raw_period)

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            title=resolved_title,
            pub_code=str(pub_code),
            record_category=data.get("record_category", SourceRecordCategory.NEWS),
            record_type=data.get("record_type", SourceRecordType.MISC),
            frequency=data.get("frequency"),
            publisher_raw=data.get("publisher_raw"),
            place_of_publication_raw=data.get("place_of_publication_raw"),
            location_id=data.get("location_id"),
            publication_period=resolved_period,
            issn_or_lccn=data.get("issn_or_lccn"),
            is_active=bool(data.get("is_active", True)),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"Publication [{self.canonical_title}] ({self.pub_code})"
