"""Path: tests/test_gda/test_model/test_source/test_probate/test_probate_inventory.py

Comprehensive unit tests for gda.model.source.probate.inventory
(EstateInventoryRecord, InventoryLineItem, and ProbateLedgerEntry).

Operational Role:
    Exercises InventoryLineItem, ProbateLedgerEntry, and EstateInventoryRecord
    creation, EstatePropertyCategory and ProbateLedgerEntryKind enum parsing,
    numeric valuation totals, flatten_items() and flatten_ledger_entries()
    tabular projections, dict/JSON round-trip serialization, and defensive
    deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.probate import EstatePropertyCategory, ProbateLedgerEntryKind
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.probate import (
    EstateInventoryRecord,
    InventoryLineItem,
    ProbateLedgerEntry,
)

__version__ = "1.0.0+build.2"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_PARENT_SID = "44444444-4444-4444-8444-444444444444"
_MID = "33333333-3333-4333-8333-333333333333"
_URN_WILL = "URN:WILL:1874:US_NH_MERRIMACK:INVENTORY_4128"
_URN_SRC = "URN:SRC:1875:US_NH_MERRIMACK:ADMIN_ACCT_4128"


@pytest.mark.unit
@pytest.mark.smoke
def test_inventory_item_ledger_and_record_roundtrip() -> None:
    """Verify InventoryLineItem, ProbateLedgerEntry, and EstateInventoryRecord round-trip."""
    now = IsoTimestamp("2026-08-02T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    appraised_dt = EventDate.create("1874-04-12")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000003"),
        name_raw="Samuel H. Abbott",
        role=AssociatedRole.WITNESS,
    )

    item1 = InventoryLineItem.create(
        line_number=1,
        item_description_raw="  Homestead farm of 80 acres in Concord  ",
        property_category="  real_estate  ",
        appraised_value_raw="$2,400.00",
        appraised_value_numeric=2400.0,
        currency_code="  usd  ",
        remarks_raw="Appraised by Selectmen",
    )
    item2 = InventoryLineItem.create(
        line_number=2,
        item_description_raw="1 yoke of working oxen",
        property_category=EstatePropertyCategory.LIVESTOCK,
        appraised_value_raw="$145.00",
        appraised_value_numeric=145.0,
    )
    item3 = InventoryLineItem.create(
        line_number=3,
        item_description_raw="Sundry old books and pamphlets",
    )

    assert item1.item_description_raw == "Homestead farm of 80 acres in Concord"
    assert item1.property_category is EstatePropertyCategory.REAL_ESTATE
    assert item2.property_category is EstatePropertyCategory.LIVESTOCK
    assert item1.currency_code == "USD"
    assert str(item1) == "Line 1: Homestead farm of 80 acres in Concord"
    assert InventoryLineItem.from_json(item1.to_json()) == item1

    item3_dict = item3.to_dict()
    for opt_key in ("appraised_value_raw", "appraised_value_numeric", "remarks_raw"):
        assert opt_key not in item3_dict
    assert InventoryLineItem.from_dict(item3_dict) == item3

    led1 = ProbateLedgerEntry.create(
        line_number=1,
        party_name_raw="  Dr. Charles P. Gage  ",
        entry_kind="  debt_paid  ",
        party_id="IND-000010",
        purpose_raw="Medical attendance in last sickness",
        amount_raw="$18.50",
        amount_numeric=18.5,
    )
    led2 = ProbateLedgerEntry.create(
        line_number=2,
        party_name_raw="John H. Abbott",
        entry_kind=ProbateLedgerEntryKind.DISTRIBUTION,
    )

    assert led1.party_name_raw == "Dr. Charles P. Gage"
    assert led1.entry_kind is ProbateLedgerEntryKind.DEBT_PAID
    assert led2.entry_kind is ProbateLedgerEntryKind.DISTRIBUTION
    assert str(led1) == "Line 1: Dr. Charles P. Gage [DEBT_PAID]"
    assert ProbateLedgerEntry.from_json(led1.to_json()) == led1

    led2_dict = led2.to_dict()
    for opt_key in ("party_id", "purpose_raw", "amount_raw", "amount_numeric"):
        assert opt_key not in led2_dict
    assert ProbateLedgerEntry.from_dict(led2_dict) == led2

    rec = EstateInventoryRecord.create(
        source_id=_SID,
        source_urn=_URN_WILL,
        description="Inventory and Appraisal of the Estate of George W. Abbott.",
        repository_id="REP-000001",
        court_name="  Merrimack County Probate Court  ",
        filing_locator="  Estate File #4128  ",
        decedent_name_raw="  George W. Abbott  ",
        record_category="probate",
        record_type="estate_inventory",
        court_location_id="LOC-000001",
        estate_file_number="4128",
        book_and_page="Inventory Book 22, p. 88",
        decedent_id="IND-000001",
        parent_probate_source_id=_PARENT_SID,
        date_appraised_or_accounted=appraised_dt,
        appraisers_or_administrators=["Samuel H. Abbott", "Arthur W. Colby"],
        total_appraised_value_raw="$2,545.00",
        total_appraised_value_numeric=2545.0,
        currency_code="  usd  ",
        items=[item1, item2, item3],
        ledger_entries=[led1, led2],
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.court_name == "Merrimack County Probate Court"
    assert rec.filing_locator == "Estate File #4128"
    assert rec.decedent_name_raw == "George W. Abbott"
    assert rec.court_location_id == LocationID("LOC-000001")
    assert rec.decedent_id == IndividualID("IND-000001")
    assert rec.parent_probate_source_id == SourceID(_PARENT_SID)
    assert rec.item_count == 3
    assert rec.ledger_entry_count == 2
    assert rec.computed_items_total == pytest.approx(2545.0)
    assert (
        str(rec) == "EstateInventoryRecord [ESTATE_INVENTORY] George W. Abbott (3 items, 2 entries)"
    )

    flat_items = rec.flatten_items()
    assert len(flat_items) == 3
    assert flat_items[0]["item_description_raw"] == "Homestead farm of 80 acres in Concord"
    assert flat_items[0]["decedent_name_raw"] == "George W. Abbott"

    flat_ledger = rec.flatten_ledger_entries()
    assert len(flat_ledger) == 2
    assert flat_ledger[0]["party_name_raw"] == "Dr. Charles P. Gage"
    assert flat_ledger[1]["party_name_raw"] == "John H. Abbott"

    payload = rec.to_dict()
    assert payload["currency_code"] == "USD"
    assert len(payload["items"]) == 3
    assert len(payload["ledger_entries"]) == 2

    restored = EstateInventoryRecord.from_dict(payload)
    assert restored == rec

    restored_json = EstateInventoryRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct ArchivalURN, AuditStamp, EventDate, InventoryLineItem, and ProbateLedgerEntry instances
    direct_urn_rec = EstateInventoryRecord.create(
        source_id=_SID,
        source_urn=ArchivalURN(_URN_WILL),
        description="Direct ArchivalURN instance check.",
        repository_id="REP-000001",
        court_name="Merrimack County Probate Court",
        filing_locator="Estate File #4128",
        decedent_name_raw="George W. Abbott",
    )
    assert direct_urn_rec.source_urn == ArchivalURN(_URN_WILL)

    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["date_appraised_or_accounted"] = appraised_dt
    direct_payload["items"] = [item1, item2, item3]
    direct_payload["ledger_entries"] = [led1, led2]
    assert EstateInventoryRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_inventory_validation_and_minimal_roundtrip() -> None:
    """Verify EstateInventoryRecord minimal round-trip and validation error branches."""
    minimal = EstateInventoryRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_SRC,
        description="Administrator's Final Account for Samuel Abbott.",
        repository_id=RepositoryID("REP-000001"),
        court_name="Merrimack County Probate Court",
        filing_locator="Docket 1862-14",
        decedent_name_raw="Samuel Abbott",
        record_category=SourceRecordCategory.LEGAL,
        record_type=SourceRecordType.ADMINISTRATION_ACCOUNT,
        media_ids=[MediaID(_MID)],
    )
    assert minimal.item_count == 0
    assert minimal.ledger_entry_count == 0
    assert minimal.computed_items_total == 0.0
    assert minimal.flatten_items() == ()
    assert minimal.flatten_ledger_entries() == ()

    min_dict = minimal.to_dict()
    for opt_key in (
        "court_location_id",
        "estate_file_number",
        "book_and_page",
        "decedent_id",
        "parent_probate_source_id",
        "date_appraised_or_accounted",
        "total_appraised_value_raw",
        "total_appraised_value_numeric",
    ):
        assert opt_key not in min_dict
    assert EstateInventoryRecord.from_dict(min_dict) == minimal

    # String date coercion check
    str_date_rec = EstateInventoryRecord.create(
        source_id=_SID,
        source_urn=_URN_SRC,
        description="String date check.",
        repository_id="REP-000001",
        court_name="Merrimack County Probate Court",
        filing_locator="Docket 1862-14",
        decedent_name_raw="Samuel Abbott",
        date_appraised_or_accounted="1875-05-01",
    )
    assert str_date_rec.date_appraised_or_accounted == EventDate.create("1875-05-01")

    # Direct constructors normalize whitespace/case
    direct_item = InventoryLineItem(
        line_number=1,
        item_description_raw="  Brass clock  ",
        currency_code="  gbp  ",
    )
    assert direct_item.item_description_raw == "Brass clock"
    assert direct_item.property_category is EstatePropertyCategory.OTHER
    assert direct_item.currency_code == "GBP"

    direct_led = ProbateLedgerEntry(
        line_number=1,
        party_name_raw="  John Smith  ",
    )
    assert direct_led.party_name_raw == "John Smith"
    assert direct_led.entry_kind is ProbateLedgerEntryKind.DEBT_PAID

    direct_rec = EstateInventoryRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        court_name="  Trimmed Court  ",
        filing_locator="  Trimmed Locator  ",
        decedent_name_raw="  Trimmed Decedent  ",
        currency_code="  gbp  ",
    )
    assert direct_rec.court_name == "Trimmed Court"
    assert direct_rec.filing_locator == "Trimmed Locator"
    assert direct_rec.decedent_name_raw == "Trimmed Decedent"
    assert direct_rec.currency_code == "GBP"

    # InventoryLineItem error branches
    with pytest.raises(ModelFormatError, match="item_description_raw"):
        InventoryLineItem.create(line_number=1, item_description_raw="   ")

    with pytest.raises(ModelFormatError, match="Invalid EstatePropertyCategory value"):
        InventoryLineItem.create(
            line_number=1, item_description_raw="Clock", property_category="INVALID_CAT"
        )

    with pytest.raises(ModelFormatError, match="Invalid currency_code"):
        InventoryLineItem.create(line_number=1, item_description_raw="Clock", currency_code="US")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        InventoryLineItem.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'line_number'"):
        InventoryLineItem.from_dict({"line_number": 1})

    with pytest.raises(ModelFormatError, match="Failed to parse InventoryLineItem JSON"):
        InventoryLineItem.from_json("{bad-json")

    # ProbateLedgerEntry error branches
    with pytest.raises(ModelFormatError, match="party_name_raw"):
        ProbateLedgerEntry.create(line_number=1, party_name_raw="   ")

    with pytest.raises(ModelFormatError, match="Invalid ProbateLedgerEntryKind value"):
        ProbateLedgerEntry.create(line_number=1, party_name_raw="Party", entry_kind="INVALID_KIND")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        ProbateLedgerEntry.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'line_number'"):
        ProbateLedgerEntry.from_dict({"line_number": 1})

    with pytest.raises(ModelFormatError, match="Failed to parse ProbateLedgerEntry JSON"):
        ProbateLedgerEntry.from_json("{bad-json")

    # EstateInventoryRecord validation branches
    with pytest.raises(ModelFormatError, match="Invalid Probate URN syntax"):
        EstateInventoryRecord.create(
            source_id=_SID,
            source_urn="URN:WILL:bad",
            description="Bad URN",
            repository_id="REP-000001",
            court_name="Court",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
        )

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        EstateInventoryRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong category",
            repository_id="REP-000001",
            court_name="Court",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
            record_category=SourceRecordCategory.VITAL,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        EstateInventoryRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong type",
            repository_id="REP-000001",
            court_name="Court",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="court_name"):
        EstateInventoryRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Empty court",
            repository_id="REP-000001",
            court_name="   ",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
        )

    with pytest.raises(ModelFormatError, match="Invalid currency_code"):
        EstateInventoryRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad currency",
            repository_id="REP-000001",
            court_name="Court",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
            currency_code="123",
        )

    with pytest.raises(ModelFormatError, match="Duplicate InventoryLineItem line_number"):
        EstateInventoryRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Duplicate items",
            repository_id="REP-000001",
            court_name="Court",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
            items=[
                {"line_number": 1, "item_description_raw": "Item A"},
                {"line_number": 1, "item_description_raw": "Item B"},
            ],
        )

    with pytest.raises(ModelFormatError, match="Duplicate ProbateLedgerEntry line_number"):
        EstateInventoryRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Duplicate ledger entries",
            repository_id="REP-000001",
            court_name="Court",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
            ledger_entries=[
                {"line_number": 1, "party_name_raw": "Party A"},
                {"line_number": 1, "party_name_raw": "Party B"},
            ],
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_appraised_or_accounted' payload"):
        EstateInventoryRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad date",
            repository_id="REP-000001",
            court_name="Court",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
            date_appraised_or_accounted=1874,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        EstateInventoryRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        EstateInventoryRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        EstateInventoryRecord.from_dict(bad_audit)

    bad_items = dict(min_dict)
    bad_items["items"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'items' must be a list or tuple"):
        EstateInventoryRecord.from_dict(bad_items)

    bad_ledger = dict(min_dict)
    bad_ledger["ledger_entries"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'ledger_entries' must be a list or tuple"):
        EstateInventoryRecord.from_dict(bad_ledger)
