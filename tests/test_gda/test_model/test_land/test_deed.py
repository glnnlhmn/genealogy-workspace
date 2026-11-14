"""Path: tests/test_gda/test_model/test_land/test_deed.py

Comprehensive unit tests for gda.model.land.deed
(LandDeedRecord, DeedParty, and LandParcel).

Operational Role:
    Exercises DeedParty, LandParcel, and LandDeedRecord creation, DeedPartyRole
    enum parsing, URN:LAND and URN:SRC resolution, category and record_type
    bounds, flatten_parties() tabular projection, dict/JSON round-trip
    serialization, and defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.land import DeedPartyRole
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.land import DeedParty, LandDeedRecord, LandParcel

__version__ = "1.0.0+build.2"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN_LAND = "URN:LAND:1848:US_NH_MERRIMACK:DEED_BK92_P314"
_URN_SRC = "URN:SRC:1851:US_NH_MERRIMACK:DEED_BK104_P18"


@pytest.mark.unit
@pytest.mark.smoke
def test_deed_party_parcel_and_record_roundtrip() -> None:
    """Verify DeedParty, LandParcel, and LandDeedRecord full metadata and serialization."""
    now = IsoTimestamp("2026-09-01T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    written = EventDate.create("1848-04-10")
    acked = EventDate.create("1848-04-11")
    recorded = EventDate.create("1848-04-15")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000005"),
        name_raw="Nathaniel Rolfe",
        role=AssociatedRole.WITNESS,
    )

    g1 = DeedParty.create(
        full_name="  Samuel H. Abbott  ",
        party_role="  grantor  ",
        individual_id="IND-000001",
        residence_raw="Concord, NH",
        residence_location_id="LOC-000001",
        relationship_to_grantee="Father",
    )
    g2 = DeedParty.create(
        full_name="Mary E. Abbott",
        party_role=DeedPartyRole.GRANTEE,
    )

    assert g1.full_name == "Samuel H. Abbott"
    assert g1.party_role is DeedPartyRole.GRANTOR
    assert g2.party_role is DeedPartyRole.GRANTEE
    assert str(g1) == "Samuel H. Abbott (GRANTOR)"
    assert DeedParty.from_json(g1.to_json()) == g1

    g2_dict = g2.to_dict()
    for opt_key in (
        "individual_id",
        "residence_raw",
        "residence_location_id",
        "relationship_to_grantee",
    ):
        assert opt_key not in g2_dict
    assert DeedParty.from_dict(g2_dict) == g2

    p1 = LandParcel.create(
        location_raw="  Concord, Merrimack County, NH  ",
        location_id="LOC-000001",
        tract_name="East Concord Intervale Lot",
        acreage_raw="45 acres, 20 rods",
        acreage_numeric=45.125,
        metes_and_bounds_summary="Beginning at a white oak on Merrimack River...",
        neighboring_landowners=["Jacob Carter", "Benjamin Kimball"],
        prior_deed_recital="Conveyed by Jeremiah Pecker, Book 61, p. 44",
    )
    p2 = LandParcel.create(
        location_raw="Bow, Merrimack County, NH",
    )

    assert p1.location_raw == "Concord, Merrimack County, NH"
    assert str(p1) == "East Concord Intervale Lot (Concord, Merrimack County, NH)"
    assert str(p2) == "Bow, Merrimack County, NH"
    assert LandParcel.from_json(p1.to_json()) == p1

    p2_dict = p2.to_dict()
    for opt_key in (
        "location_id",
        "tract_name",
        "acreage_raw",
        "acreage_numeric",
        "metes_and_bounds_summary",
        "prior_deed_recital",
    ):
        assert opt_key not in p2_dict
    assert LandParcel.from_dict(p2_dict) == p2

    rec = LandDeedRecord.create(
        source_id=_SID,
        source_urn=_URN_LAND,
        description="Warranty deed from Samuel H. Abbott to Mary E. Abbott.",
        repository_id="REP-000001",
        office_title="  Merrimack County Registry of Deeds  ",
        recording_locator="  Book 92, Page 314  ",
        date_written=written,
        grantors=[g1],
        grantees=[g2],
        parcel=p1,
        record_category="land",
        record_type="deed_indenture",
        office_location_id="LOC-000001",
        recorder_or_deputy="Reuben T. Leavitt, Register",
        deed_book="92",
        page_number="314",
        instrument_number="1848-0412",
        date_acknowledged=acked,
        date_recorded=recorded,
        consideration_amount="$650.00",
        dower_relinquished=True,
        additional_parcels=[p2],
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.office_title == "Merrimack County Registry of Deeds"
    assert rec.recording_locator == "Book 92, Page 314"
    assert rec.office_location_id == LocationID("LOC-000001")
    assert rec.grantor_count == 1
    assert rec.grantee_count == 1
    assert rec.all_parcels == (p1, p2)
    assert (
        str(rec)
        == "LandDeedRecord [DEED_INDENTURE] Samuel H. Abbott -> Mary E. Abbott (Book 92, Page 314)"
    )

    flat = rec.flatten_parties()
    assert len(flat) == 2
    assert flat[0]["full_name"] == "Samuel H. Abbott"
    assert flat[0]["party_role"] == "GRANTOR"
    assert flat[1]["full_name"] == "Mary E. Abbott"
    assert flat[1]["party_role"] == "GRANTEE"

    payload = rec.to_dict()
    assert payload["consideration_amount"] == "$650.00"
    assert payload["dower_relinquished"] is True
    assert len(payload["additional_parcels"]) == 1

    restored = LandDeedRecord.from_dict(payload)
    assert restored == rec

    restored_json = LandDeedRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct ArchivalURN, AuditStamp, EventDate, DeedParty, and LandParcel instances
    direct_urn_rec = LandDeedRecord.create(
        source_id=_SID,
        source_urn=ArchivalURN(_URN_LAND),
        description="Direct ArchivalURN instance check.",
        repository_id="REP-000001",
        office_title="Merrimack County Registry of Deeds",
        recording_locator="Book 92, Page 314",
        date_written=written,
        grantors=[g1],
        grantees=[g2],
        parcel=p1,
    )
    assert direct_urn_rec.source_urn == ArchivalURN(_URN_LAND)

    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["date_written"] = written
    direct_payload["date_acknowledged"] = acked
    direct_payload["date_recorded"] = recorded
    direct_payload["grantors"] = [g1]
    direct_payload["grantees"] = [g2]
    direct_payload["parcel"] = p1
    direct_payload["additional_parcels"] = [p2]
    assert LandDeedRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_deed_validation_and_minimal_roundtrip() -> None:
    """Verify LandDeedRecord minimal round-trip and validation error branches."""
    minimal = LandDeedRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_SRC,
        description="Quitclaim deed recorded in Book 104.",
        repository_id=RepositoryID("REP-000001"),
        office_title="Merrimack County Registry of Deeds",
        recording_locator="Book 104, Page 18",
        date_written="1851-09-02",
        grantors=[{"full_name": "George W. Abbott"}],
        grantees=[{"full_name": "John H. Abbott"}],
        parcel={"location_raw": "Concord, NH"},
        record_category=SourceRecordCategory.PROPERTY,
        record_type=SourceRecordType.QUITCLAIM_DEED,
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "office_location_id",
        "recorder_or_deputy",
        "deed_book",
        "page_number",
        "instrument_number",
        "date_acknowledged",
        "date_recorded",
        "consideration_amount",
        "dower_relinquished",
    ):
        assert opt_key not in min_dict
    assert LandDeedRecord.from_dict(min_dict) == minimal

    # Direct constructors normalize whitespace and guard empty grantors/grantees
    direct_party = DeedParty(full_name="  Hannah Kimball  ", party_role=DeedPartyRole.GRANTEE)
    assert direct_party.full_name == "Hannah Kimball"
    assert direct_party.party_role is DeedPartyRole.GRANTEE

    direct_parcel = LandParcel(location_raw="  Hopkinton, NH  ")
    assert direct_parcel.location_raw == "Hopkinton, NH"

    direct_rec = LandDeedRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        office_title="  Trimmed Office  ",
        recording_locator="  Trimmed Locator  ",
        date_written=minimal.date_written,
        grantors=minimal.grantors,
        grantees=minimal.grantees,
        parcel=minimal.parcel,
    )
    assert direct_rec.office_title == "Trimmed Office"
    assert direct_rec.recording_locator == "Trimmed Locator"

    with pytest.raises(ModelFormatError, match="requires at least one grantor"):
        LandDeedRecord(
            source_id=SourceID(_SID),
            source_urn=minimal.source_urn,
            description="Empty grantors",
            repository_id=RepositoryID("REP-000001"),
            audit=minimal.audit,
            office_title="Office",
            recording_locator="Loc",
            date_written=minimal.date_written,
            grantors=(),
            grantees=minimal.grantees,
            parcel=minimal.parcel,
        )

    with pytest.raises(ModelFormatError, match="requires at least one grantee"):
        LandDeedRecord(
            source_id=SourceID(_SID),
            source_urn=minimal.source_urn,
            description="Empty grantees",
            repository_id=RepositoryID("REP-000001"),
            audit=minimal.audit,
            office_title="Office",
            recording_locator="Loc",
            date_written=minimal.date_written,
            grantors=minimal.grantors,
            grantees=(),
            parcel=minimal.parcel,
        )

    # DeedParty error branches
    with pytest.raises(ModelFormatError, match="full_name"):
        DeedParty.create(full_name="   ")

    with pytest.raises(ModelFormatError, match="Invalid DeedPartyRole value"):
        DeedParty.create(full_name="Test", party_role="WITNESS")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        DeedParty.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'full_name'"):
        DeedParty.from_dict({})

    with pytest.raises(ModelFormatError, match="Failed to parse DeedParty JSON"):
        DeedParty.from_json("{bad-json")

    # LandParcel error branches
    with pytest.raises(ModelFormatError, match="location_raw"):
        LandParcel.create(location_raw="   ")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        LandParcel.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'location_raw'"):
        LandParcel.from_dict({})

    with pytest.raises(ModelFormatError, match="'neighboring_landowners' must be a list or tuple"):
        LandParcel.from_dict({"location_raw": "Concord", "neighboring_landowners": "bad"})

    with pytest.raises(ModelFormatError, match="Failed to parse LandParcel JSON"):
        LandParcel.from_json("{bad-json")

    # LandDeedRecord validation branches
    with pytest.raises(ModelFormatError, match="Invalid Land URN syntax"):
        LandDeedRecord.create(
            source_id=_SID,
            source_urn="URN:LAND:bad",
            description="Bad URN",
            repository_id="REP-000001",
            office_title="Office",
            recording_locator="Loc",
            date_written="1851-09-02",
            grantors=[{"full_name": "A"}],
            grantees=[{"full_name": "B"}],
            parcel={"location_raw": "Concord"},
        )

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        LandDeedRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong category",
            repository_id="REP-000001",
            office_title="Office",
            recording_locator="Loc",
            date_written="1851-09-02",
            grantors=[{"full_name": "A"}],
            grantees=[{"full_name": "B"}],
            parcel={"location_raw": "Concord"},
            record_category=SourceRecordCategory.CENSUS,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        LandDeedRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong type",
            repository_id="REP-000001",
            office_title="Office",
            recording_locator="Loc",
            date_written="1851-09-02",
            grantors=[{"full_name": "A"}],
            grantees=[{"full_name": "B"}],
            parcel={"location_raw": "Concord"},
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="office_title"):
        LandDeedRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Empty office",
            repository_id="REP-000001",
            office_title="   ",
            recording_locator="Loc",
            date_written="1851-09-02",
            grantors=[{"full_name": "A"}],
            grantees=[{"full_name": "B"}],
            parcel={"location_raw": "Concord"},
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_written' payload"):
        LandDeedRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad date",
            repository_id="REP-000001",
            office_title="Office",
            recording_locator="Loc",
            date_written=1851,  # type: ignore[arg-type]
            grantors=[{"full_name": "A"}],
            grantees=[{"full_name": "B"}],
            parcel={"location_raw": "Concord"},
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        LandDeedRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        LandDeedRecord.from_dict({"source_id": _SID})

    bad_grantors = dict(min_dict)
    bad_grantors["grantors"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'grantors' must be a list or tuple"):
        LandDeedRecord.from_dict(bad_grantors)

    bad_grantees = dict(min_dict)
    bad_grantees["grantees"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'grantees' must be a list or tuple"):
        LandDeedRecord.from_dict(bad_grantees)

    bad_extra = dict(min_dict)
    bad_extra["additional_parcels"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'additional_parcels' must be a list or tuple"):
        LandDeedRecord.from_dict(bad_extra)

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        LandDeedRecord.from_dict(bad_audit)
