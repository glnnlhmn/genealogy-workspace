"""Path: tests/test_gda/test_model/test_probate/test_will.py

Comprehensive unit tests for gda.model.probate.will
(ProbateRecord and WillBequest).

Operational Role:
    Exercises WillBequest and ProbateRecord creation, URN:WILL and URN:SRC
    resolution, BequestType enum parsing, category and record_type bounds,
    duplicate bequest prevention, dict/JSON round-trip serialization, and
    defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.probate import BequestType
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.probate import ProbateRecord, WillBequest

__version__ = "1.1.0+build.1"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN_WILL = "URN:WILL:1874:US_NH_MERRIMACK:ESTATE_4128"
_URN_SRC = "URN:SRC:1874:US_NH_MERRIMACK:PROBATE_BK45_P112"


@pytest.mark.unit
@pytest.mark.smoke
def test_will_bequest_and_probate_record_roundtrip() -> None:
    """Verify WillBequest and ProbateRecord full metadata and serialization."""
    now = IsoTimestamp("2026-08-01T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    written = EventDate.create("1873-10-14")
    probated = EventDate.create("1874-03-24")
    letters = EventDate.create("1874-03-25")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000002"),
        name_raw="Mary E. Abbott",
        role=AssociatedRole.WITNESS,
    )

    b1 = WillBequest.create(
        item_number=1,
        beneficiary_name_raw="  Mary E. Abbott  ",
        property_or_amount_raw="  Homestead farm of 80 acres in Concord  ",
        beneficiary_id="IND-000002",
        relationship_raw="beloved wife",
        bequest_type="  real_estate  ",
        conditions_raw="during her natural life",
    )
    b2 = WillBequest.create(
        item_number=2,
        beneficiary_name_raw="John H. Abbott",
        property_or_amount_raw="$500 in lawful money",
        bequest_type=BequestType.MONETARY,
    )

    assert b1.beneficiary_name_raw == "Mary E. Abbott"
    assert b1.property_or_amount_raw == "Homestead farm of 80 acres in Concord"
    assert b1.bequest_type is BequestType.REAL_ESTATE
    assert b2.bequest_type is BequestType.MONETARY
    assert str(b1) == "Item 1: Mary E. Abbott (Homestead farm of 80 acres in Concord)"
    assert WillBequest.from_json(b1.to_json()) == b1

    b2_dict = b2.to_dict()
    for opt_key in ("beneficiary_id", "relationship_raw", "conditions_raw"):
        assert opt_key not in b2_dict
    assert WillBequest.from_dict(b2_dict) == b2

    rec = ProbateRecord.create(
        source_id=_SID,
        source_urn=_URN_WILL,
        description="Last Will and Testament of George W. Abbott, proved March 1874.",
        repository_id="REP-000001",
        court_name="  Merrimack County Probate Court  ",
        filing_locator="  Estate File #4128  ",
        decedent_name_raw="  George W. Abbott  ",
        record_category="probate",
        record_type="last_will_and_testament",
        court_location_id="LOC-000001",
        register_or_clerk="Isaac A. Hill, Register",
        estate_file_number="4128",
        book_and_page="Will Book 45, p. 112",
        docket_term="March Term 1874",
        decedent_id="IND-000001",
        decedent_residence_raw="Concord, Merrimack County, NH",
        decedent_residence_id="LOC-000002",
        decedent_condition_or_trade="Yeoman",
        date_written=written,
        date_probated=probated,
        date_letters_granted=letters,
        provisions_summary="Names wife Mary E. Abbott executrix; divides homestead and $500.",
        bequests=[b1, b2],
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
    assert rec.decedent_residence_id == LocationID("LOC-000002")
    assert rec.bequest_count == 2
    assert (
        str(rec) == "ProbateRecord [LAST_WILL_AND_TESTAMENT] George W. Abbott (Estate File #4128)"
    )

    payload = rec.to_dict()
    assert payload["court_name"] == "Merrimack County Probate Court"
    assert len(payload["bequests"]) == 2

    restored = ProbateRecord.from_dict(payload)
    assert restored == rec

    restored_json = ProbateRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct ArchivalURN, AuditStamp, EventDate, and WillBequest objects
    direct_urn_rec = ProbateRecord.create(
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
    direct_payload["date_written"] = written
    direct_payload["date_probated"] = probated
    direct_payload["date_letters_granted"] = letters
    direct_payload["bequests"] = [b1, b2]
    assert ProbateRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_probate_record_validation_and_minimal_roundtrip() -> None:
    """Verify ProbateRecord minimal round-trip and validation error branches."""
    minimal = ProbateRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_SRC,
        description="Letters of Administration on estate of Samuel Abbott.",
        repository_id=RepositoryID("REP-000001"),
        court_name="Merrimack County Probate Court",
        filing_locator="Docket 1862-14",
        decedent_name_raw="Samuel Abbott",
        record_category=SourceRecordCategory.LEGAL,
        record_type=SourceRecordType.LETTERS_ADMINISTRATION,
        media_ids=[MediaID(_MID)],
    )
    assert minimal.bequest_count == 0
    min_dict = minimal.to_dict()
    for opt_key in (
        "court_location_id",
        "register_or_clerk",
        "estate_file_number",
        "book_and_page",
        "docket_term",
        "decedent_id",
        "decedent_residence_raw",
        "decedent_residence_id",
        "decedent_condition_or_trade",
        "date_written",
        "date_probated",
        "date_letters_granted",
        "provisions_summary",
    ):
        assert opt_key not in min_dict
    assert ProbateRecord.from_dict(min_dict) == minimal

    # Direct constructor normalizes whitespace on WillBequest and ProbateRecord
    direct_b = WillBequest(
        item_number=1,
        beneficiary_name_raw="  Hannah Kimball  ",
        property_or_amount_raw="  Silver spoons  ",
    )
    assert direct_b.beneficiary_name_raw == "Hannah Kimball"
    assert direct_b.property_or_amount_raw == "Silver spoons"
    assert direct_b.bequest_type is BequestType.PERSONAL_PROPERTY

    direct_rec = ProbateRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        court_name="  Trimmed Court  ",
        filing_locator="  Trimmed Locator  ",
        decedent_name_raw="  Trimmed Decedent  ",
    )
    assert direct_rec.court_name == "Trimmed Court"
    assert direct_rec.filing_locator == "Trimmed Locator"
    assert direct_rec.decedent_name_raw == "Trimmed Decedent"

    # WillBequest error branches
    with pytest.raises(ModelFormatError, match="beneficiary_name_raw"):
        WillBequest.create(item_number=1, beneficiary_name_raw="   ", property_or_amount_raw="$10")

    with pytest.raises(ModelFormatError, match="property_or_amount_raw"):
        WillBequest.create(item_number=1, beneficiary_name_raw="Heir", property_or_amount_raw="   ")

    with pytest.raises(ModelFormatError, match="Invalid BequestType value"):
        WillBequest.create(
            item_number=1,
            beneficiary_name_raw="Heir",
            property_or_amount_raw="$10",
            bequest_type="INVALID_KIND",
        )

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        WillBequest.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'item_number'"):
        WillBequest.from_dict({"item_number": 1})

    with pytest.raises(ModelFormatError, match="Failed to parse WillBequest JSON"):
        WillBequest.from_json("{bad-json")

    # ProbateRecord validation branches
    with pytest.raises(ModelFormatError, match="Invalid Probate URN syntax"):
        ProbateRecord.create(
            source_id=_SID,
            source_urn="URN:WILL:bad",
            description="Bad URN",
            repository_id="REP-000001",
            court_name="Court",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
        )

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        ProbateRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong category",
            repository_id="REP-000001",
            court_name="Court",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
            record_category=SourceRecordCategory.CENSUS,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        ProbateRecord.create(
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
        ProbateRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Empty court",
            repository_id="REP-000001",
            court_name="   ",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
        )

    with pytest.raises(ModelFormatError, match="Duplicate WillBequest item_number"):
        ProbateRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Duplicate bequests",
            repository_id="REP-000001",
            court_name="Court",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
            bequests=[
                {"item_number": 1, "beneficiary_name_raw": "A", "property_or_amount_raw": "$1"},
                {"item_number": 1, "beneficiary_name_raw": "B", "property_or_amount_raw": "$2"},
            ],
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_written' payload"):
        ProbateRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad date",
            repository_id="REP-000001",
            court_name="Court",
            filing_locator="Loc",
            decedent_name_raw="Decedent",
            date_written=1873,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        ProbateRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        ProbateRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        ProbateRecord.from_dict(bad_audit)

    bad_bequests = dict(min_dict)
    bad_bequests["bequests"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'bequests' must be a list or tuple"):
        ProbateRecord.from_dict(bad_bequests)
