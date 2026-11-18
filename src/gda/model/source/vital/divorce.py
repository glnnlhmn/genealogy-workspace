"""Path: src/gda/model/source/vital/divorce.py

Civil divorce decree, divorce report, docket entry, and annulment models.

Operational Role:
    Defines DivorceRecord extending SourceRecord to capture primary documentary
    evidence from civil divorce decrees, state vital divorce reports, court
    docket entries, and annulment judgments (aligned with
    schemas/sources/divorce_report.schema.json).
"""

from __future__ import annotations

from typing import Any, ClassVar, cast

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import DivorceDecreeType, LegalPlaintiff
from gda.core.errors import ModelFormatError
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone
from gda.util.enums import coerce_enum

__version__ = "1.0.0+build.3"

__all__ = [
    "DivorceRecord",
]

_DIVORCE_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.LEGAL,
        SourceRecordCategory.VITAL,
    }
)

_DIVORCE_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.DIVORCE_REPORT,
        SourceRecordType.DIVORCE_DECREE,
        SourceRecordType.DOCKET_ENTRY,
        SourceRecordType.ANNULMENT,
    }
)


def _deserialize_event_date(raw: Any, field_name: str) -> EventDate:
    """Coerce an EventDate instance, dictionary, or compact date string."""
    if isinstance(raw, EventDate):
        return raw
    if isinstance(raw, (dict, str)):
        return EventDate.from_dict(raw)
    raise ModelFormatError(f"Invalid '{field_name}' payload: expected EventDate, dict, or str.")


def _parse_decree_type(raw: DivorceDecreeType | str) -> DivorceDecreeType:
    """Resolve DivorceDecreeType from enum member, value string, or member name."""
    try:
        return coerce_enum(DivorceDecreeType, raw, field_name="decree_type")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid DivorceDecreeType value: '{raw}'.") from err


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class DivorceRecord(SourceRecord):
    """Primary archival record documenting a civil divorce decree, report, or annulment."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.LEGAL,
        description="High-level archival domain category (LEGAL or VITAL).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.DIVORCE_REPORT,
        description="Specific divorce documentary record classification.",
    )
    court_name: str = Field(
        ...,
        description="Verbatim name of the court granting or recording the decree.",
    )
    husband_name_raw: str = Field(
        ...,
        description="Verbatim full name of the husband or first party.",
    )
    wife_name_raw: str = Field(
        ...,
        description="Verbatim full name of the wife or second party.",
    )
    date_decree_granted: EventDate = Field(
        ...,
        description="Date the divorce decree or annulment was granted.",
    )
    docket_number: str | None = Field(
        default=None,
        description="Court docket or case file number.",
    )
    state_file_number: str | None = Field(
        default=None,
        description="State vital statistics divorce report file number.",
    )
    jurisdiction_raw: str | None = Field(
        default=None,
        description="Verbatim county and state jurisdiction of the court.",
    )
    jurisdiction_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID of the court jurisdiction.",
    )
    husband_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the husband if linked.",
    )
    wife_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the wife if linked.",
    )
    wife_maiden_name_raw: str | None = Field(
        default=None,
        description="Verbatim maiden surname of the wife if stated or restored.",
    )
    date_of_marriage: EventDate | None = Field(
        default=None,
        description="Date of the dissolved marriage if stated in the decree.",
    )
    place_of_marriage_raw: str | None = Field(
        default=None,
        description="Verbatim place where the dissolved marriage occurred.",
    )
    date_of_separation: EventDate | None = Field(
        default=None,
        description="Recorded date of marital separation.",
    )
    plaintiff: LegalPlaintiff | None = Field(
        default=None,
        description="Party who initiated the proceeding (Husband, Wife, Other).",
    )
    decree_type: DivorceDecreeType = Field(
        default=DivorceDecreeType.ABSOLUTE,
        description="Legal classification of the decree (Absolute, Bed and Board, Annulment, etc.).",
    )
    legal_grounds: str | None = Field(
        default=None,
        description="Verbatim statutory grounds alleged or granted (e.g., 'Desertion', 'Cruelty').",
    )
    minor_children_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of minor children affected by the decree.",
    )
    alimony_awarded: bool | None = Field(
        default=None,
        description="True if alimony or maintenance was awarded.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _DIVORCE_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _DIVORCE_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, court name, and spouse name boundaries."""
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

        for field_name in ("court_name", "husband_name_raw", "wife_name_raw"):
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
        court_name: str,
        husband_name_raw: str,
        wife_name_raw: str,
        date_decree_granted: EventDate | dict[str, Any] | str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.LEGAL,
        record_type: SourceRecordType | str = SourceRecordType.DIVORCE_REPORT,
        docket_number: str | None = None,
        state_file_number: str | None = None,
        jurisdiction_raw: str | None = None,
        jurisdiction_id: LocationID | str | None = None,
        husband_id: IndividualID | str | None = None,
        wife_id: IndividualID | str | None = None,
        wife_maiden_name_raw: str | None = None,
        date_of_marriage: EventDate | dict[str, Any] | str | None = None,
        place_of_marriage_raw: str | None = None,
        date_of_separation: EventDate | dict[str, Any] | str | None = None,
        plaintiff: LegalPlaintiff | str | None = None,
        decree_type: DivorceDecreeType | str = DivorceDecreeType.ABSOLUTE,
        legal_grounds: str | None = None,
        minor_children_count: int | None = None,
        alimony_awarded: bool | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> DivorceRecord:
        """Factory constructor instantiating a validated DivorceRecord."""
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
        res_jur_id = (
            jurisdiction_id
            if (jurisdiction_id is None or isinstance(jurisdiction_id, LocationID))
            else LocationID(jurisdiction_id)
        )
        res_husb_id = (
            husband_id
            if (husband_id is None or isinstance(husband_id, IndividualID))
            else IndividualID(husband_id)
        )
        res_wife_id = (
            wife_id
            if (wife_id is None or isinstance(wife_id, IndividualID))
            else IndividualID(wife_id)
        )
        res_plaintiff = (
            coerce_enum(LegalPlaintiff, plaintiff, field_name="plaintiff")
            if plaintiff is not None
            else None
        )
        res_decree_type = _parse_decree_type(decree_type)

        res_decree_date = _deserialize_event_date(date_decree_granted, "date_decree_granted")
        res_dom = (
            _deserialize_event_date(date_of_marriage, "date_of_marriage")
            if date_of_marriage is not None
            else None
        )
        res_sep = (
            _deserialize_event_date(date_of_separation, "date_of_separation")
            if date_of_separation is not None
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
            court_name=court_name,
            husband_name_raw=husband_name_raw,
            wife_name_raw=wife_name_raw,
            date_decree_granted=res_decree_date,
            docket_number=docket_number,
            state_file_number=state_file_number,
            jurisdiction_raw=jurisdiction_raw,
            jurisdiction_id=res_jur_id,
            husband_id=res_husb_id,
            wife_id=res_wife_id,
            wife_maiden_name_raw=wife_maiden_name_raw,
            date_of_marriage=res_dom,
            place_of_marriage_raw=place_of_marriage_raw,
            date_of_separation=res_sep,
            plaintiff=res_plaintiff,
            decree_type=res_decree_type,
            legal_grounds=legal_grounds,
            minor_children_count=minor_children_count,
            alimony_awarded=alimony_awarded,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize DivorceRecord to a dictionary."""
        return super().to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DivorceRecord:
        """Deserialize a dictionary payload into a DivorceRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("DivorceRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        court_name = data.get("court_name")
        husband_name = data.get("husband_name_raw")
        wife_name = data.get("wife_name_raw")
        raw_decree_date = data.get("date_decree_granted")

        if not all(
            (
                sid,
                raw_urn,
                desc,
                rep,
                audit_payload,
                court_name,
                husband_name,
                wife_name,
                raw_decree_date,
            )
        ):
            raise ModelFormatError(
                "DivorceRecord requires source_id, source_urn, description, repository_id, "
                "audit, court_name, husband_name_raw, wife_name_raw, and date_decree_granted."
            )

        if not isinstance(audit_payload, (AuditStamp, dict)):
            raise ModelFormatError("DivorceRecord audit must be an AuditStamp or dictionary.")
        audit_obj = AuditStamp.from_dict(audit_payload)

        tombstone_payload = data.get("tombstone")
        tombstone_obj = (
            Tombstone.from_dict(tombstone_payload, id_cls=SourceID)
            if isinstance(tombstone_payload, dict)
            else None
        )

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            court_name=str(court_name),
            husband_name_raw=str(husband_name),
            wife_name_raw=str(wife_name),
            date_decree_granted=cast(Any, raw_decree_date),
            record_category=data.get("record_category", SourceRecordCategory.LEGAL),
            record_type=data.get("record_type", SourceRecordType.DIVORCE_REPORT),
            docket_number=data.get("docket_number"),
            state_file_number=data.get("state_file_number"),
            jurisdiction_raw=data.get("jurisdiction_raw"),
            jurisdiction_id=data.get("jurisdiction_id"),
            husband_id=data.get("husband_id"),
            wife_id=data.get("wife_id"),
            wife_maiden_name_raw=data.get("wife_maiden_name_raw"),
            date_of_marriage=data.get("date_of_marriage"),
            place_of_marriage_raw=data.get("place_of_marriage_raw"),
            date_of_separation=data.get("date_of_separation"),
            plaintiff=data.get("plaintiff"),
            decree_type=data.get("decree_type", DivorceDecreeType.ABSOLUTE),
            legal_grounds=data.get("legal_grounds"),
            minor_children_count=data.get("minor_children_count"),
            alimony_awarded=data.get("alimony_awarded"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return (
            f"DivorceRecord [{self.husband_name_raw} v. {self.wife_name_raw}] "
            f"({self.date_decree_granted})"
        )
