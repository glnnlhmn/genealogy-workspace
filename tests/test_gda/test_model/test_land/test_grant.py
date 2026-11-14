"""Path: tests/test_gda/test_model/test_land/test_grant.py

Comprehensive unit tests for gda.model.land.grant.LandGrantRecord.

Operational Role:
    Exercises LandGrantRecord creation, LandGrantBasis enum parsing, URN:LAND
    and URN:SRC resolution, category and record_type bounds, PLSS aliquot &
    bounty land fields, dict/JSON round-trip serialization, and defensive
    deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.land import LandGrantBasis
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.land import LandGrantRecord, LandParcel

__version__ = "1.0.0+build.2"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN_LAND = "URN:LAND:1834:US_OH_CHILLICOTHE:GLO_PATENT_4821"
_URN_SRC = "URN:SRC:1754:US_NH_MASONIAN:PROPRIETARY_GRANT_12"


@pytest.mark.unit
@pytest.mark.smoke
def test_land_grant_record_roundtrip() -> None:
    """Verify LandGrantRecord full metadata and serialization."""
    now = IsoTimestamp("2026-09-02T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    warrant_dt = EventDate.create("1832-05-14")
    survey_dt = EventDate.create("1833-08-22")
    patent_dt = EventDate.create("1834-03-10")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000001"),
        name_raw="George W. Abbott",
        role=AssociatedRole.PRIMARY,
    )
    parcel = LandParcel.create(
        location_raw="Ross County, Ohio",
        location_id="LOC-000010",
        acreage_raw="160 acres",
        acreage_numeric=160.0,
    )

    rec = LandGrantRecord.create(
        source_id=_SID,
        source_urn=_URN_LAND,
        description="United States General Land Office Bounty Land Patent #4821.",
        repository_id="REP-000001",
        issuing_authority="  United States General Land Office  ",
        instrument_locator="  BLM GLO Patent #4821  ",
        patentee_name_raw="  George W. Abbott  ",
        parcel=parcel,
        record_category="military",
        record_type="patent",
        land_office_raw="Chillicothe Land Office, Ohio",
        office_location_id="LOC-000010",
        patent_or_warrant_number="4821",
        certificate_or_entry_number="Cert. 1192",
        grant_basis="  bounty_land  ",
        military_service_reference="Private, Capt. Stickney's Co., NH Militia, War of 1812",
        patentee_id="IND-000001",
        assignee_name_raw="Samuel H. Abbott",
        assignee_id="IND-000002",
        surveyor_or_chain_carriers=["Israel Ludlow, Deputy Surveyor", "John Doe, Chainman"],
        date_warrant_or_entry=warrant_dt,
        date_surveyed=survey_dt,
        date_patented=patent_dt,
        aliquot_description="NW 1/4 of Section 14, Township 8N, Range 21W",
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.issuing_authority == "United States General Land Office"
    assert rec.instrument_locator == "BLM GLO Patent #4821"
    assert rec.patentee_name_raw == "George W. Abbott"
    assert rec.grant_basis is LandGrantBasis.BOUNTY_LAND
    assert rec.office_location_id == LocationID("LOC-000010")
    assert rec.patentee_id == IndividualID("IND-000001")
    assert rec.assignee_id == IndividualID("IND-000002")
    assert str(rec) == "LandGrantRecord [PATENT] George W. Abbott (BLM GLO Patent #4821)"

    payload = rec.to_dict()
    assert payload["grant_basis"] == "BOUNTY_LAND"
    assert len(payload["surveyor_or_chain_carriers"]) == 2

    restored = LandGrantRecord.from_dict(payload)
    assert restored == rec

    restored_json = LandGrantRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct ArchivalURN, LandGrantBasis, AuditStamp, EventDate, and LandParcel instances
    direct_urn_rec = LandGrantRecord.create(
        source_id=_SID,
        source_urn=ArchivalURN(_URN_LAND),
        description="Direct ArchivalURN and LandGrantBasis instance check.",
        repository_id="REP-000001",
        issuing_authority="United States General Land Office",
        instrument_locator="BLM GLO Patent #4821",
        patentee_name_raw="George W. Abbott",
        parcel=parcel,
        grant_basis=LandGrantBasis.HOMESTEAD,
    )
    assert direct_urn_rec.source_urn == ArchivalURN(_URN_LAND)
    assert direct_urn_rec.grant_basis is LandGrantBasis.HOMESTEAD

    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["date_warrant_or_entry"] = warrant_dt
    direct_payload["date_surveyed"] = survey_dt
    direct_payload["date_patented"] = patent_dt
    direct_payload["parcel"] = parcel
    assert LandGrantRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_land_grant_validation_and_minimal_roundtrip() -> None:
    """Verify LandGrantRecord minimal round-trip and validation error branches."""
    minimal = LandGrantRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_SRC,
        description="Masonian Proprietary Grant Lot 12.",
        repository_id=RepositoryID("REP-000001"),
        issuing_authority="Proprietors of Masonian Patent",
        instrument_locator="Masonian Papers Vol. 3, p. 12",
        patentee_name_raw="Nathaniel Abbott",
        parcel={"location_raw": "Concord, NH"},
        record_category=SourceRecordCategory.PROPERTY,
        record_type=SourceRecordType.WARRANT,
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "land_office_raw",
        "office_location_id",
        "patent_or_warrant_number",
        "certificate_or_entry_number",
        "grant_basis",
        "military_service_reference",
        "patentee_id",
        "assignee_name_raw",
        "assignee_id",
        "date_warrant_or_entry",
        "date_surveyed",
        "date_patented",
        "aliquot_description",
    ):
        assert opt_key not in min_dict
    assert LandGrantRecord.from_dict(min_dict) == minimal

    # Direct constructor trims required string fields
    direct = LandGrantRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        issuing_authority="  Trimmed Authority  ",
        instrument_locator="  Trimmed Locator  ",
        patentee_name_raw="  Trimmed Patentee  ",
        parcel=minimal.parcel,
    )
    assert direct.issuing_authority == "Trimmed Authority"
    assert direct.instrument_locator == "Trimmed Locator"
    assert direct.patentee_name_raw == "Trimmed Patentee"

    # Validation branches
    with pytest.raises(ModelFormatError, match="Invalid Land URN syntax"):
        LandGrantRecord.create(
            source_id=_SID,
            source_urn="URN:LAND:bad",
            description="Bad URN",
            repository_id="REP-000001",
            issuing_authority="Auth",
            instrument_locator="Loc",
            patentee_name_raw="Patentee",
            parcel={"location_raw": "Concord"},
        )

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        LandGrantRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong category",
            repository_id="REP-000001",
            issuing_authority="Auth",
            instrument_locator="Loc",
            patentee_name_raw="Patentee",
            parcel={"location_raw": "Concord"},
            record_category=SourceRecordCategory.VITAL,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        LandGrantRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong type",
            repository_id="REP-000001",
            issuing_authority="Auth",
            instrument_locator="Loc",
            patentee_name_raw="Patentee",
            parcel={"location_raw": "Concord"},
            record_type=SourceRecordType.DEED_INDENTURE,
        )

    with pytest.raises(ModelFormatError, match="issuing_authority"):
        LandGrantRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Empty authority",
            repository_id="REP-000001",
            issuing_authority="   ",
            instrument_locator="Loc",
            patentee_name_raw="Patentee",
            parcel={"location_raw": "Concord"},
        )

    with pytest.raises(ModelFormatError, match="Invalid LandGrantBasis value"):
        LandGrantRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad grant_basis",
            repository_id="REP-000001",
            issuing_authority="Auth",
            instrument_locator="Loc",
            patentee_name_raw="Patentee",
            parcel={"location_raw": "Concord"},
            grant_basis="INVALID_BASIS",
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_patented' payload"):
        LandGrantRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad date",
            repository_id="REP-000001",
            issuing_authority="Auth",
            instrument_locator="Loc",
            patentee_name_raw="Patentee",
            parcel={"location_raw": "Concord"},
            date_patented=1834,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        LandGrantRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        LandGrantRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        LandGrantRecord.from_dict(bad_audit)

    bad_surveyors = dict(min_dict)
    bad_surveyors["surveyor_or_chain_carriers"] = "not-a-list"
    with pytest.raises(
        ModelFormatError, match="'surveyor_or_chain_carriers' must be a list or tuple"
    ):
        LandGrantRecord.from_dict(bad_surveyors)
