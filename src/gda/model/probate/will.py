"""Path: src/gda/model/probate/will.py

Last wills and testaments, codicils, letters testamentary/administration, and probate dockets.

Operational Role:
    Defines WillBequest (structured devise, legacy, or guardianship provision inside a
    testamentary instrument) and ProbateRecord (extending SourceRecord) to capture primary
    documentary evidence from wills, codicils, letters of administration/testamentary,
    Orphans' Court entries, and probate docket filings (aligned with
    schemas/sources/probate_record.schema.json).
"""

from __future__ import annotations

import json
import re
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.probate import BequestType
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
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
    "ProbateRecord",
    "WillBequest",
]

_PROBATE_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.PROBATE,
        SourceRecordCategory.LEGAL,
    }
)

_PROBATE_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.LAST_WILL_AND_TESTAMENT,
        SourceRecordType.CODICIL,
        SourceRecordType.LETTERS_TESTAMENTARY,
        SourceRecordType.LETTERS_ADMINISTRATION,
        SourceRecordType.ORPHANS_COURT_ENTRY,
        SourceRecordType.DOCKET_ENTRY,
    }
)

_WILL_URN_PATTERN: re.Pattern[str] = re.compile(r"^URN:WILL:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$")


def _resolve_probate_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into ArchivalURN (URN:WILL:...) or SourceURN (URN:SRC:...)."""
    if isinstance(raw, ArchivalURN):
        return raw
    token = str(raw).strip()
    if token.startswith("URN:WILL:"):
        if not _WILL_URN_PATTERN.match(token):
            raise ModelFormatError(
                f"Invalid Probate URN syntax: '{token}'. "
                "Must match 'URN:WILL:<YEAR>:<JURISDICTION>:<LOCATOR>'."
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


def _parse_bequest_type(raw: BequestType | str) -> BequestType:
    """Resolve BequestType by enum instance, exact value, or uppercase member name."""
    if isinstance(raw, BequestType):
        return raw
    token = str(raw).strip().upper()
    for member in BequestType:
        if token in (member.name, member.value):
            return member
    raise ModelFormatError(f"Invalid BequestType value: '{raw}'.")


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class WillBequest(IntrospectableMixin):
    """Single structured devise, legacy, or guardianship clause in a will or codicil."""

    item_number: int = Field(
        ...,
        ge=1,
        description="1-based clause or item number within the testamentary instrument.",
    )
    beneficiary_name_raw: str = Field(
        ...,
        description="Verbatim name of the legatee, devisee, heir, or ward named in the clause.",
    )
    property_or_amount_raw: str = Field(
        ...,
        description="Verbatim bequest description, tract, chattel, or monetary legacy.",
    )
    beneficiary_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the beneficiary if linked.",
    )
    relationship_raw: str | None = Field(
        default=None,
        description="Verbatim kinship or status phrase (e.g., 'beloved wife', 'eldest son').",
    )
    bequest_type: BequestType = Field(
        default=BequestType.PERSONAL_PROPERTY,
        description="Classification of bequest (REAL_ESTATE, PERSONAL_PROPERTY, MONETARY, RESIDUARY, GUARDIANSHIP, OTHER).",
    )
    conditions_raw: str | None = Field(
        default=None,
        description="Verbatim life-estate, age-majority, or payment conditions attached to the gift.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty beneficiary and bequest description hygiene."""
        clean_ben = self.beneficiary_name_raw.strip()
        if not clean_ben:
            raise ModelFormatError(
                "WillBequest 'beneficiary_name_raw' cannot be empty or whitespace.",
                details={"item_number": self.item_number},
            )
        if clean_ben != self.beneficiary_name_raw:
            object.__setattr__(self, "beneficiary_name_raw", clean_ben)

        clean_prop = self.property_or_amount_raw.strip()
        if not clean_prop:
            raise ModelFormatError(
                "WillBequest 'property_or_amount_raw' cannot be empty or whitespace.",
                details={"item_number": self.item_number},
            )
        if clean_prop != self.property_or_amount_raw:
            object.__setattr__(self, "property_or_amount_raw", clean_prop)

    @classmethod
    def create(
        cls,
        item_number: int,
        beneficiary_name_raw: str,
        property_or_amount_raw: str,
        beneficiary_id: IndividualID | str | None = None,
        relationship_raw: str | None = None,
        bequest_type: BequestType | str = BequestType.PERSONAL_PROPERTY,
        conditions_raw: str | None = None,
    ) -> WillBequest:
        """Factory constructor instantiating a validated WillBequest."""
        res_ben = (
            beneficiary_id
            if (beneficiary_id is None or isinstance(beneficiary_id, IndividualID))
            else IndividualID(beneficiary_id)
        )
        return cls(
            item_number=item_number,
            beneficiary_name_raw=beneficiary_name_raw,
            property_or_amount_raw=property_or_amount_raw,
            beneficiary_id=res_ben,
            relationship_raw=relationship_raw,
            bequest_type=_parse_bequest_type(bequest_type),
            conditions_raw=conditions_raw,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize WillBequest to a dictionary."""
        data: dict[str, Any] = {
            "item_number": self.item_number,
            "beneficiary_name_raw": self.beneficiary_name_raw,
            "property_or_amount_raw": self.property_or_amount_raw,
            "bequest_type": self.bequest_type.value,
        }
        if self.beneficiary_id is not None:
            data["beneficiary_id"] = str(self.beneficiary_id)
        if self.relationship_raw is not None:
            data["relationship_raw"] = self.relationship_raw
        if self.conditions_raw is not None:
            data["conditions_raw"] = self.conditions_raw
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WillBequest:
        """Deserialize a dictionary payload into a WillBequest."""
        if not isinstance(data, dict):
            raise ModelFormatError("WillBequest payload must be a dictionary.")
        item_num = data.get("item_number")
        ben = data.get("beneficiary_name_raw")
        prop = data.get("property_or_amount_raw")
        if item_num is None or ben is None or prop is None:
            raise ModelFormatError(
                "WillBequest requires 'item_number', 'beneficiary_name_raw', "
                "and 'property_or_amount_raw'."
            )
        return cls.create(
            item_number=int(item_num),
            beneficiary_name_raw=str(ben),
            property_or_amount_raw=str(prop),
            beneficiary_id=data.get("beneficiary_id"),
            relationship_raw=data.get("relationship_raw"),
            bequest_type=data.get("bequest_type", BequestType.PERSONAL_PROPERTY),
            conditions_raw=data.get("conditions_raw"),
        )

    def to_json(self) -> str:
        """Serialize WillBequest to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> WillBequest:
        """Deserialize a JSON string directly into a WillBequest."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse WillBequest JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return (
            f"Item {self.item_number}: {self.beneficiary_name_raw} ({self.property_or_amount_raw})"
        )


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class ProbateRecord(SourceRecord):
    """Primary archival record documenting a will, codicil, letters, or probate court entry."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.PROBATE,
        description="High-level archival domain category (PROBATE or LEGAL).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.LAST_WILL_AND_TESTAMENT,
        description="Specific probate instrument classification.",
    )
    court_name: str = Field(
        ...,
        description="Verbatim name of the Probate, Surrogate, or Orphans' Court.",
    )
    filing_locator: str = Field(
        ...,
        description="Primary archival filing call number, packet ID, or docket locator.",
    )
    decedent_name_raw: str = Field(
        ...,
        description="Verbatim name of the testator, intestate decedent, or minor ward.",
    )
    court_location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the court's civil jurisdiction.",
    )
    register_or_clerk: str | None = Field(
        default=None,
        description="Name of the Register of Wills, Surrogate, or Probate Clerk.",
    )
    estate_file_number: str | None = Field(
        default=None,
        description="Official probate estate packet or docket file number.",
    )
    book_and_page: str | None = Field(
        default=None,
        description="Recorded will book, administration book, and page/folio reference.",
    )
    docket_term: str | None = Field(
        default=None,
        description="Court term or session designation (e.g., 'May Term 1874').",
    )
    decedent_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the decedent or testator.",
    )
    decedent_residence_raw: str | None = Field(
        default=None,
        description="Verbatim town, township, or county of residence stated in the instrument.",
    )
    decedent_residence_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the decedent's residence.",
    )
    decedent_condition_or_trade: str | None = Field(
        default=None,
        description="Verbatim occupation or marital/social condition (e.g., 'yeoman', 'widow').",
    )
    date_written: EventDate | None = Field(
        default=None,
        description="Date the will or codicil was signed and witnessed.",
    )
    date_probated: EventDate | None = Field(
        default=None,
        description="Date the will was proved and admitted to probate.",
    )
    date_letters_granted: EventDate | None = Field(
        default=None,
        description="Date letters testamentary, administration, or guardianship were issued.",
    )
    provisions_summary: str | None = Field(
        default=None,
        description="Narrative abstract of key testamentary dispositions, executors, and witnesses.",
    )
    bequests: tuple[WillBequest, ...] = Field(
        default=(),
        description="Optional ordered tuple of structured devise and legacy clauses.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _PROBATE_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _PROBATE_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, required strings, and unique bequest item_numbers."""
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

        for field_name in ("court_name", "filing_locator", "decedent_name_raw"):
            raw_val = getattr(self, field_name)
            cleaned = raw_val.strip()
            if not cleaned:
                raise ModelFormatError(
                    f"{self.__class__.__name__} '{field_name}' cannot be empty or whitespace."
                )
            if cleaned != raw_val:
                object.__setattr__(self, field_name, cleaned)

        seen_items: set[int] = set()
        for bequest in self.bequests:
            if bequest.item_number in seen_items:
                raise ModelFormatError(
                    f"Duplicate WillBequest item_number {bequest.item_number} within probate record."
                )
            seen_items.add(bequest.item_number)

    @property
    def bequest_count(self) -> int:
        """Return the number of structured bequests recorded on this instrument."""
        return len(self.bequests)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        court_name: str,
        filing_locator: str,
        decedent_name_raw: str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.PROBATE,
        record_type: SourceRecordType | str = SourceRecordType.LAST_WILL_AND_TESTAMENT,
        court_location_id: LocationID | str | None = None,
        register_or_clerk: str | None = None,
        estate_file_number: str | None = None,
        book_and_page: str | None = None,
        docket_term: str | None = None,
        decedent_id: IndividualID | str | None = None,
        decedent_residence_raw: str | None = None,
        decedent_residence_id: LocationID | str | None = None,
        decedent_condition_or_trade: str | None = None,
        date_written: EventDate | dict[str, Any] | str | None = None,
        date_probated: EventDate | dict[str, Any] | str | None = None,
        date_letters_granted: EventDate | dict[str, Any] | str | None = None,
        provisions_summary: str | None = None,
        bequests: list[WillBequest | dict[str, Any]] | tuple[WillBequest, ...] | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> ProbateRecord:
        """Factory constructor instantiating a validated ProbateRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_probate_urn(source_urn)
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
        res_court_loc = (
            court_location_id
            if (court_location_id is None or isinstance(court_location_id, LocationID))
            else LocationID(court_location_id)
        )
        res_dec_id = (
            decedent_id
            if (decedent_id is None or isinstance(decedent_id, IndividualID))
            else IndividualID(decedent_id)
        )
        res_dec_loc = (
            decedent_residence_id
            if (decedent_residence_id is None or isinstance(decedent_residence_id, LocationID))
            else LocationID(decedent_residence_id)
        )
        res_written = (
            _deserialize_event_date(date_written, "date_written")
            if date_written is not None
            else None
        )
        res_probated = (
            _deserialize_event_date(date_probated, "date_probated")
            if date_probated is not None
            else None
        )
        res_letters = (
            _deserialize_event_date(date_letters_granted, "date_letters_granted")
            if date_letters_granted is not None
            else None
        )

        resolved_bequests: tuple[WillBequest, ...] = tuple(
            b if isinstance(b, WillBequest) else WillBequest.from_dict(b) for b in (bequests or ())
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
            filing_locator=filing_locator,
            decedent_name_raw=decedent_name_raw,
            court_location_id=res_court_loc,
            register_or_clerk=register_or_clerk,
            estate_file_number=estate_file_number,
            book_and_page=book_and_page,
            docket_term=docket_term,
            decedent_id=res_dec_id,
            decedent_residence_raw=decedent_residence_raw,
            decedent_residence_id=res_dec_loc,
            decedent_condition_or_trade=decedent_condition_or_trade,
            date_written=res_written,
            date_probated=res_probated,
            date_letters_granted=res_letters,
            provisions_summary=provisions_summary,
            bequests=resolved_bequests,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize ProbateRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "court_name": self.court_name,
                "filing_locator": self.filing_locator,
                "decedent_name_raw": self.decedent_name_raw,
                "bequests": [b.to_dict() for b in self.bequests],
            }
        )
        if self.court_location_id is not None:
            data["court_location_id"] = str(self.court_location_id)
        if self.register_or_clerk is not None:
            data["register_or_clerk"] = self.register_or_clerk
        if self.estate_file_number is not None:
            data["estate_file_number"] = self.estate_file_number
        if self.book_and_page is not None:
            data["book_and_page"] = self.book_and_page
        if self.docket_term is not None:
            data["docket_term"] = self.docket_term
        if self.decedent_id is not None:
            data["decedent_id"] = str(self.decedent_id)
        if self.decedent_residence_raw is not None:
            data["decedent_residence_raw"] = self.decedent_residence_raw
        if self.decedent_residence_id is not None:
            data["decedent_residence_id"] = str(self.decedent_residence_id)
        if self.decedent_condition_or_trade is not None:
            data["decedent_condition_or_trade"] = self.decedent_condition_or_trade
        if self.date_written is not None:
            data["date_written"] = self.date_written.to_dict()
        if self.date_probated is not None:
            data["date_probated"] = self.date_probated.to_dict()
        if self.date_letters_granted is not None:
            data["date_letters_granted"] = self.date_letters_granted.to_dict()
        if self.provisions_summary is not None:
            data["provisions_summary"] = self.provisions_summary
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProbateRecord:
        """Deserialize a dictionary payload into a ProbateRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("ProbateRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        court_name = data.get("court_name")
        locator = data.get("filing_locator")
        decedent = data.get("decedent_name_raw")

        if not all((sid, raw_urn, desc, rep, audit_payload, court_name, locator, decedent)):
            raise ModelFormatError(
                "ProbateRecord requires source_id, source_urn, description, repository_id, "
                "audit, court_name, filing_locator, and decedent_name_raw."
            )

        if isinstance(audit_payload, AuditStamp):
            audit_obj = audit_payload
        elif isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )
        else:
            raise ModelFormatError("ProbateRecord audit must be an AuditStamp or dictionary.")

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

        raw_bequests = data.get("bequests", [])
        if not isinstance(raw_bequests, (list, tuple)):
            raise ModelFormatError("ProbateRecord 'bequests' must be a list or tuple.")

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            court_name=str(court_name),
            filing_locator=str(locator),
            decedent_name_raw=str(decedent),
            record_category=data.get("record_category", SourceRecordCategory.PROBATE),
            record_type=data.get("record_type", SourceRecordType.LAST_WILL_AND_TESTAMENT),
            court_location_id=data.get("court_location_id"),
            register_or_clerk=data.get("register_or_clerk"),
            estate_file_number=data.get("estate_file_number"),
            book_and_page=data.get("book_and_page"),
            docket_term=data.get("docket_term"),
            decedent_id=data.get("decedent_id"),
            decedent_residence_raw=data.get("decedent_residence_raw"),
            decedent_residence_id=data.get("decedent_residence_id"),
            decedent_condition_or_trade=data.get("decedent_condition_or_trade"),
            date_written=data.get("date_written"),
            date_probated=data.get("date_probated"),
            date_letters_granted=data.get("date_letters_granted"),
            provisions_summary=data.get("provisions_summary"),
            bequests=list(raw_bequests),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"ProbateRecord [{self.record_type.value}] {self.decedent_name_raw} ({self.filing_locator})"
