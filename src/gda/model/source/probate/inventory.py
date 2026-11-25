"""Path: src/gda/model/source/probate/inventory.py

Estate appraisal inventory, vendue list, and administration accounting models.

Operational Role:
    Defines InventoryLineItem (single appraised chattel or real property row),
    ProbateLedgerEntry (single receipt, creditor claim paid, or heir distribution row),
    and EstateInventoryRecord (extending SourceRecord) for collection-wide estate
    inventories and administration accounts with flatten_items() and
    flatten_ledger_entries() tabular projections (aligned with
    schemas/sources/probate_record.schema.json).
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums import coerce_enum
from gda.core.enums.probate import EstatePropertyCategory, ProbateLedgerEntryKind
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

__version__ = "1.0.0+build.6"

__all__ = [
    "EstateInventoryRecord",
    "InventoryLineItem",
    "ProbateLedgerEntry",
]

# Allowed category and record type sets for estate inventories and accounts
_INVENTORY_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.PROBATE,
        SourceRecordCategory.LEGAL,
    }
)

_INVENTORY_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.ESTATE_INVENTORY,
        SourceRecordType.ADMINISTRATION_ACCOUNT,
        SourceRecordType.ORPHANS_COURT_ENTRY,
    }
)

_WILL_URN_PATTERN: re.Pattern[str] = URN_REGEXES["WILL"]


# ==============================================================================
# 1. COERCION & NORMALIZATION HELPERS
# ==============================================================================


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


def _opt_event_date(raw: Any, field_name: str) -> EventDate | None:
    """Coerce an optional EventDate input or return None when absent."""
    return _deserialize_event_date(raw, field_name) if raw is not None else None


def _parse_probate_enum[E](enum_cls: type[E], raw: Any, field_name: str) -> E:
    """Resolve a probate StrEnum by instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(enum_cls, raw, field_name=field_name)  # type: ignore[type-var]
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid {field_name} value: '{raw}'.") from err


def _coerce_id[TID](val: TID | str, id_cls: type[TID]) -> TID:
    """Coerce a required typed ID or string token into id_cls."""
    return val if isinstance(val, id_cls) else id_cls(val)  # type: ignore[call-arg]


def _opt_id[TID](val: TID | str | None, id_cls: type[TID]) -> TID | None:
    """Coerce an optional typed ID or string token into id_cls, or return None."""
    if val is None:
        return None
    return val if isinstance(val, id_cls) else id_cls(val)  # type: ignore[call-arg]


def _opt_float(val: float | int | None) -> float | None:
    """Convert an optional numeric value to float or return None."""
    return float(val) if val is not None else None


def _coerce_items_tuple(
    items: Iterable[InventoryLineItem | dict[str, Any]] | None,
) -> tuple[InventoryLineItem, ...]:
    """Hydrate an optional sequence of InventoryLineItem objects or dicts into a tuple."""
    if not items:
        return ()
    return tuple(
        i if isinstance(i, InventoryLineItem) else InventoryLineItem.from_dict(i) for i in items
    )


def _coerce_ledger_tuple(
    entries: Iterable[ProbateLedgerEntry | dict[str, Any]] | None,
) -> tuple[ProbateLedgerEntry, ...]:
    """Hydrate an optional sequence of ProbateLedgerEntry objects or dicts into a tuple."""
    if not entries:
        return ()
    return tuple(
        e if isinstance(e, ProbateLedgerEntry) else ProbateLedgerEntry.from_dict(e) for e in entries
    )


def _coerce_media_list(media_ids: Iterable[MediaID | str] | None) -> list[MediaID]:
    """Hydrate an optional sequence of MediaID instances or strings into a list."""
    if not media_ids:
        return []
    return [m if isinstance(m, MediaID) else MediaID(m) for m in media_ids]


# ==============================================================================
# 2. INVENTORY LINE ITEM & LEDGER ENTRY VALUE OBJECTS
# ==============================================================================


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class InventoryLineItem(IntrospectableMixin):
    """Single appraised real or personal property row in an estate inventory."""

    line_number: int = Field(
        ...,
        ge=1,
        description="1-based line number on the appraisal schedule or vendue bill.",
    )
    item_description_raw: str = Field(
        ...,
        description="Verbatim description of the chattel, livestock, note, or real estate parcel.",
    )
    property_category: EstatePropertyCategory = Field(
        default=EstatePropertyCategory.OTHER,
        description="Taxonomic asset class (REAL_ESTATE, LIVESTOCK, HOUSEHOLD, TOOLS, NOTES_RECEIVABLE, CASH, OTHER).",
    )
    appraised_value_raw: str | None = Field(
        default=None,
        description="Verbatim appraised valuation string (e.g., '$145.00', '£42 10s 0d').",
    )
    appraised_value_numeric: float | None = Field(
        default=None,
        ge=0.0,
        description="Normalized decimal valuation for tabular summation.",
    )
    currency_code: str = Field(
        default="USD",
        description="Three-letter currency code (e.g., USD, GBP).",
    )
    remarks_raw: str | None = Field(
        default=None,
        description="Verbatim buyer name at vendue, condition note, or debtor reference.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty item description and normalized currency code."""
        clean_desc = self.item_description_raw.strip()
        if not clean_desc:
            raise ModelFormatError(
                "InventoryLineItem 'item_description_raw' cannot be empty or whitespace.",
                details={"line_number": self.line_number},
            )
        if clean_desc != self.item_description_raw:
            object.__setattr__(self, "item_description_raw", clean_desc)

        clean_curr = self.currency_code.strip().upper()
        if len(clean_curr) != 3 or not clean_curr.isalpha():
            raise ModelFormatError(
                f"Invalid currency_code '{self.currency_code}': must be 3 alphabetic letters."
            )
        if clean_curr != self.currency_code:
            object.__setattr__(self, "currency_code", clean_curr)

    @classmethod
    def create(
        cls,
        line_number: int,
        item_description_raw: str,
        property_category: EstatePropertyCategory | str = EstatePropertyCategory.OTHER,
        appraised_value_raw: str | None = None,
        appraised_value_numeric: float | int | None = None,
        currency_code: str = "USD",
        remarks_raw: str | None = None,
    ) -> InventoryLineItem:
        """Factory constructor instantiating a validated InventoryLineItem."""
        return cls(
            line_number=line_number,
            item_description_raw=item_description_raw,
            property_category=_parse_probate_enum(
                EstatePropertyCategory, property_category, "EstatePropertyCategory"
            ),
            appraised_value_raw=appraised_value_raw,
            appraised_value_numeric=_opt_float(appraised_value_numeric),
            currency_code=currency_code.strip().upper(),
            remarks_raw=remarks_raw,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize InventoryLineItem to a dictionary."""
        data: dict[str, Any] = {
            "line_number": self.line_number,
            "item_description_raw": self.item_description_raw,
            "property_category": self.property_category.value,
            "currency_code": self.currency_code,
        }
        if self.appraised_value_raw is not None:
            data["appraised_value_raw"] = self.appraised_value_raw
        if self.appraised_value_numeric is not None:
            data["appraised_value_numeric"] = self.appraised_value_numeric
        if self.remarks_raw is not None:
            data["remarks_raw"] = self.remarks_raw
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InventoryLineItem:
        """Deserialize a dictionary payload into an InventoryLineItem."""
        if not isinstance(data, dict):
            raise ModelFormatError("InventoryLineItem payload must be a dictionary.")
        line_num = data.get("line_number")
        desc = data.get("item_description_raw")
        if line_num is None or desc is None:
            raise ModelFormatError(
                "InventoryLineItem requires 'line_number' and 'item_description_raw'."
            )
        return cls.create(
            line_number=int(line_num),
            item_description_raw=str(desc),
            property_category=data.get("property_category", EstatePropertyCategory.OTHER),
            appraised_value_raw=data.get("appraised_value_raw"),
            appraised_value_numeric=data.get("appraised_value_numeric"),
            currency_code=str(data.get("currency_code", "USD")),
            remarks_raw=data.get("remarks_raw"),
        )

    def to_json(self) -> str:
        """Serialize InventoryLineItem to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> InventoryLineItem:
        """Deserialize a JSON string directly into an InventoryLineItem."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse InventoryLineItem JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"Line {self.line_number}: {self.item_description_raw}"


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class ProbateLedgerEntry(IntrospectableMixin):
    """Single receipt, debt paid, expense, or heir distribution in an administration account."""

    line_number: int = Field(
        ...,
        ge=1,
        description="1-based entry sequence number in the administration or guardian account.",
    )
    party_name_raw: str = Field(
        ...,
        description="Verbatim name of the creditor, debtor, physician, undertaker, or distributee.",
    )
    entry_kind: ProbateLedgerEntryKind = Field(
        default=ProbateLedgerEntryKind.DEBT_PAID,
        description="Accounting line classification (RECEIPT, DEBT_PAID, EXPENSE, DISTRIBUTION).",
    )
    party_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID if linked to a person entity.",
    )
    purpose_raw: str | None = Field(
        default=None,
        description="Verbatim voucher description (e.g., 'Coffin and funeral', 'Distributive share').",
    )
    amount_raw: str | None = Field(
        default=None,
        description="Verbatim monetary amount string recorded in the account.",
    )
    amount_numeric: float | None = Field(
        default=None,
        ge=0.0,
        description="Normalized decimal amount for ledger reconciliation.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty party_name_raw hygiene."""
        clean_party = self.party_name_raw.strip()
        if not clean_party:
            raise ModelFormatError(
                "ProbateLedgerEntry 'party_name_raw' cannot be empty or whitespace.",
                details={"line_number": self.line_number},
            )
        if clean_party != self.party_name_raw:
            object.__setattr__(self, "party_name_raw", clean_party)

    @classmethod
    def create(
        cls,
        line_number: int,
        party_name_raw: str,
        entry_kind: ProbateLedgerEntryKind | str = ProbateLedgerEntryKind.DEBT_PAID,
        party_id: IndividualID | str | None = None,
        purpose_raw: str | None = None,
        amount_raw: str | None = None,
        amount_numeric: float | int | None = None,
    ) -> ProbateLedgerEntry:
        """Factory constructor instantiating a validated ProbateLedgerEntry."""
        return cls(
            line_number=line_number,
            party_name_raw=party_name_raw,
            entry_kind=_parse_probate_enum(
                ProbateLedgerEntryKind, entry_kind, "ProbateLedgerEntryKind"
            ),
            party_id=_opt_id(party_id, IndividualID),
            purpose_raw=purpose_raw,
            amount_raw=amount_raw,
            amount_numeric=_opt_float(amount_numeric),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize ProbateLedgerEntry to a dictionary."""
        data: dict[str, Any] = {
            "line_number": self.line_number,
            "party_name_raw": self.party_name_raw,
            "entry_kind": self.entry_kind.value,
        }
        if self.party_id is not None:
            data["party_id"] = str(self.party_id)
        if self.purpose_raw is not None:
            data["purpose_raw"] = self.purpose_raw
        if self.amount_raw is not None:
            data["amount_raw"] = self.amount_raw
        if self.amount_numeric is not None:
            data["amount_numeric"] = self.amount_numeric
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProbateLedgerEntry:
        """Deserialize a dictionary payload into a ProbateLedgerEntry."""
        if not isinstance(data, dict):
            raise ModelFormatError("ProbateLedgerEntry payload must be a dictionary.")
        line_num = data.get("line_number")
        party = data.get("party_name_raw")
        if line_num is None or party is None:
            raise ModelFormatError(
                "ProbateLedgerEntry requires 'line_number' and 'party_name_raw'."
            )
        return cls.create(
            line_number=int(line_num),
            party_name_raw=str(party),
            entry_kind=data.get("entry_kind", ProbateLedgerEntryKind.DEBT_PAID),
            party_id=data.get("party_id"),
            purpose_raw=data.get("purpose_raw"),
            amount_raw=data.get("amount_raw"),
            amount_numeric=data.get("amount_numeric"),
        )

    def to_json(self) -> str:
        """Serialize ProbateLedgerEntry to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> ProbateLedgerEntry:
        """Deserialize a JSON string directly into a ProbateLedgerEntry."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse ProbateLedgerEntry JSON string: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"Line {self.line_number}: {self.party_name_raw} [{self.entry_kind.value}]"


# ==============================================================================
# 3. ESTATE INVENTORY RECORD DOMAIN MODEL
# ==============================================================================


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class EstateInventoryRecord(SourceRecord):
    """Collection-wide estate appraisal inventory or administration accounting record."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.PROBATE,
        description="High-level archival domain category (PROBATE or LEGAL).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.ESTATE_INVENTORY,
        description="Specific accounting classification (ESTATE_INVENTORY, ADMINISTRATION_ACCOUNT, ORPHANS_COURT_ENTRY).",
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
        description="Verbatim name of the decedent whose estate is appraised or settled.",
    )
    court_location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the court's civil jurisdiction.",
    )
    estate_file_number: str | None = Field(
        default=None,
        description="Official probate estate packet or docket file number.",
    )
    book_and_page: str | None = Field(
        default=None,
        description="Recorded inventory/account book and page/folio reference.",
    )
    decedent_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the decedent.",
    )
    parent_probate_source_id: SourceID | None = Field(
        default=None,
        description="Optional foreign key linking back to the main ProbateRecord (will or letters).",
    )
    date_appraised_or_accounted: EventDate | None = Field(
        default=None,
        description="Date the inventory was sworn/appraised or the account was settled.",
    )
    appraisers_or_administrators: tuple[str, ...] = Field(
        default=(),
        description="Ordered tuple of sworn appraisers, executors, or administrators.",
    )
    total_appraised_value_raw: str | None = Field(
        default=None,
        description="Verbatim total valuation or account balance stated at the foot of the schedule.",
    )
    total_appraised_value_numeric: float | None = Field(
        default=None,
        ge=0.0,
        description="Normalized decimal total valuation.",
    )
    currency_code: str = Field(
        default="USD",
        description="Three-letter currency code (e.g., USD, GBP).",
    )
    items: tuple[InventoryLineItem, ...] = Field(
        default=(),
        description="Ordered tuple of appraised property items.",
    )
    ledger_entries: tuple[ProbateLedgerEntry, ...] = Field(
        default=(),
        description="Ordered tuple of administration receipts, debts paid, and heir distributions.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _INVENTORY_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _INVENTORY_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, required strings, currency, and line uniqueness."""
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

        clean_curr = self.currency_code.strip().upper()
        if len(clean_curr) != 3 or not clean_curr.isalpha():
            raise ModelFormatError(
                f"Invalid currency_code '{self.currency_code}': must be 3 alphabetic letters."
            )
        if clean_curr != self.currency_code:
            object.__setattr__(self, "currency_code", clean_curr)

        seen_item_lines: set[int] = set()
        for item in self.items:
            if item.line_number in seen_item_lines:
                raise ModelFormatError(
                    f"Duplicate InventoryLineItem line_number {item.line_number} within record."
                )
            seen_item_lines.add(item.line_number)

        seen_ledger_lines: set[int] = set()
        for entry in self.ledger_entries:
            if entry.line_number in seen_ledger_lines:
                raise ModelFormatError(
                    f"Duplicate ProbateLedgerEntry line_number {entry.line_number} within record."
                )
            seen_ledger_lines.add(entry.line_number)

    @property
    def item_count(self) -> int:
        """Return total number of appraised inventory line items."""
        return len(self.items)

    @property
    def ledger_entry_count(self) -> int:
        """Return total number of accounting ledger entries."""
        return len(self.ledger_entries)

    @property
    def computed_items_total(self) -> float:
        """Return the sum of non-null numeric valuations across items."""
        return sum(
            item.appraised_value_numeric
            for item in self.items
            if item.appraised_value_numeric is not None
        )

    def flatten_items(self) -> tuple[dict[str, Any], ...]:
        """Flatten estate header context with each inventory item for tabular indexing."""
        header: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "court_name": self.court_name,
            "filing_locator": self.filing_locator,
            "decedent_name_raw": self.decedent_name_raw,
            "decedent_id": str(self.decedent_id) if self.decedent_id else None,
            "parent_probate_source_id": (
                str(self.parent_probate_source_id) if self.parent_probate_source_id else None
            ),
        }
        return tuple({**header, **item.to_dict()} for item in self.items)

    def flatten_ledger_entries(self) -> tuple[dict[str, Any], ...]:
        """Flatten estate header context with each accounting ledger entry for FAN-club indexing."""
        header: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "court_name": self.court_name,
            "filing_locator": self.filing_locator,
            "decedent_name_raw": self.decedent_name_raw,
            "decedent_id": str(self.decedent_id) if self.decedent_id else None,
            "parent_probate_source_id": (
                str(self.parent_probate_source_id) if self.parent_probate_source_id else None
            ),
        }
        return tuple({**header, **entry.to_dict()} for entry in self.ledger_entries)

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
        record_type: SourceRecordType | str = SourceRecordType.ESTATE_INVENTORY,
        court_location_id: LocationID | str | None = None,
        estate_file_number: str | None = None,
        book_and_page: str | None = None,
        decedent_id: IndividualID | str | None = None,
        parent_probate_source_id: SourceID | str | None = None,
        date_appraised_or_accounted: EventDate | dict[str, Any] | str | None = None,
        appraisers_or_administrators: list[str] | tuple[str, ...] | None = None,
        total_appraised_value_raw: str | None = None,
        total_appraised_value_numeric: float | int | None = None,
        currency_code: str = "USD",
        items: list[InventoryLineItem | dict[str, Any]]
        | tuple[InventoryLineItem, ...]
        | None = None,
        ledger_entries: (
            list[ProbateLedgerEntry | dict[str, Any]] | tuple[ProbateLedgerEntry, ...] | None
        ) = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> EstateInventoryRecord:
        """Factory constructor instantiating a validated EstateInventoryRecord."""
        return cls(
            source_id=_coerce_id(source_id, SourceID),
            source_urn=_resolve_probate_urn(source_urn),
            record_category=coerce_enum(
                SourceRecordCategory, record_category, field_name="record_category"
            ),
            record_type=coerce_enum(SourceRecordType, record_type, field_name="record_type"),
            description=description.strip(),
            repository_id=_coerce_id(repository_id, RepositoryID),
            audit=audit or AuditStamp.now(),
            media_ids=_coerce_media_list(media_ids),
            associated_people=associated_people or [],
            tombstone=tombstone,
            court_name=court_name,
            filing_locator=filing_locator,
            decedent_name_raw=decedent_name_raw,
            court_location_id=_opt_id(court_location_id, LocationID),
            estate_file_number=estate_file_number,
            book_and_page=book_and_page,
            decedent_id=_opt_id(decedent_id, IndividualID),
            parent_probate_source_id=_opt_id(parent_probate_source_id, SourceID),
            date_appraised_or_accounted=_opt_event_date(
                date_appraised_or_accounted, "date_appraised_or_accounted"
            ),
            appraisers_or_administrators=tuple(appraisers_or_administrators or ()),
            total_appraised_value_raw=total_appraised_value_raw,
            total_appraised_value_numeric=_opt_float(total_appraised_value_numeric),
            currency_code=currency_code.strip().upper(),
            items=_coerce_items_tuple(items),
            ledger_entries=_coerce_ledger_tuple(ledger_entries),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize EstateInventoryRecord to a dictionary."""
        data = super().to_dict()
        data["appraisers_or_administrators"] = list(self.appraisers_or_administrators)
        data["items"] = [i.to_dict() for i in self.items]
        data["ledger_entries"] = [e.to_dict() for e in self.ledger_entries]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EstateInventoryRecord:
        """Deserialize a dictionary payload into an EstateInventoryRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("EstateInventoryRecord payload must be a dictionary.")

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
                "EstateInventoryRecord requires source_id, source_urn, description, repository_id, "
                "audit, court_name, filing_locator, and decedent_name_raw."
            )

        if not isinstance(audit_payload, (AuditStamp, dict)):
            raise ModelFormatError(
                "EstateInventoryRecord audit must be an AuditStamp or dictionary."
            )
        audit_obj = AuditStamp.from_dict(audit_payload)

        tombstone_payload = data.get("tombstone")
        tombstone_obj = (
            Tombstone.from_dict(tombstone_payload, id_cls=SourceID)
            if isinstance(tombstone_payload, dict)
            else None
        )

        raw_items = data.get("items", [])
        if not isinstance(raw_items, (list, tuple)):
            raise ModelFormatError("EstateInventoryRecord 'items' must be a list or tuple.")

        raw_ledger = data.get("ledger_entries", [])
        if not isinstance(raw_ledger, (list, tuple)):
            raise ModelFormatError(
                "EstateInventoryRecord 'ledger_entries' must be a list or tuple."
            )

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            court_name=str(court_name),
            filing_locator=str(locator),
            decedent_name_raw=str(decedent),
            record_category=data.get("record_category", SourceRecordCategory.PROBATE),
            record_type=data.get("record_type", SourceRecordType.ESTATE_INVENTORY),
            court_location_id=data.get("court_location_id"),
            estate_file_number=data.get("estate_file_number"),
            book_and_page=data.get("book_and_page"),
            decedent_id=data.get("decedent_id"),
            parent_probate_source_id=data.get("parent_probate_source_id"),
            date_appraised_or_accounted=data.get("date_appraised_or_accounted"),
            appraisers_or_administrators=data.get("appraisers_or_administrators", []),
            total_appraised_value_raw=data.get("total_appraised_value_raw"),
            total_appraised_value_numeric=data.get("total_appraised_value_numeric"),
            currency_code=str(data.get("currency_code", "USD")),
            items=list(raw_items),
            ledger_entries=list(raw_ledger),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return (
            f"EstateInventoryRecord [{self.record_type.value}] {self.decedent_name_raw} "
            f"({self.item_count} items, {self.ledger_entry_count} entries)"
        )
