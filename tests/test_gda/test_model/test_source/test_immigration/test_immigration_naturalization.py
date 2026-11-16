"""Path: tests/test_gda/test_model/test_source/test_immigration/test_immigration_naturalization.py

Comprehensive unit tests for gda.model.source.immigration.naturalization
(NaturalizationRecord and NaturalizationWitness).

Operational Role:
    Exercises NaturalizationWitness and NaturalizationRecord creation,
    URN:NATURALIZATION and URN:SRC resolution, NaturalizationStage enum parsing,
    category and record_type bounds, dict/JSON round-trip serialization, and
    defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.immigration import NaturalizationStage
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.immigration import NaturalizationRecord, NaturalizationWitness

__version__ = "1.0.0+build.2"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN_NAT = "URN:NATURALIZATION:1898:US_NH_USDC:PETITION_V12_P88"
_URN_SRC = "URN:SRC:1895:US_NH_MERRIMACK:DECLARATION_412"


@pytest.mark.unit
@pytest.mark.smoke
def test_naturalization_witness_and_record_roundtrip() -> None:
    """Verify NaturalizationWitness and NaturalizationRecord full metadata and serialization."""
    now = IsoTimestamp("2026-10-02T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    event_dt = EventDate.create("1898-10-12")
    dob = EventDate.create("1865-03-17")
    arr_dt = EventDate.create("1892-09-18")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000010"),
        name_raw="Patrick Murphy",
        role=AssociatedRole.PRIMARY,
    )

    w1 = NaturalizationWitness.create(
        name="  Michael Murphy  ",
        individual_id="IND-000011",
        occupation="Stonecutter",
        residence="Concord, NH",
    )
    w2 = NaturalizationWitness.create(
        name="Thomas F. Hennessey",
    )

    assert w1.name == "Michael Murphy"
    assert str(w1) == "Michael Murphy"
    assert NaturalizationWitness.from_json(w1.to_json()) == w1

    w2_dict = w2.to_dict()
    for opt_key in ("individual_id", "occupation", "residence"):
        assert opt_key not in w2_dict
    assert NaturalizationWitness.from_dict(w2_dict) == w2

    rec = NaturalizationRecord.create(
        source_id=_SID,
        source_urn=_URN_NAT,
        description="Petition for Naturalization of Patrick Murphy in U.S. District Court, NH.",
        repository_id="REP-000001",
        court_name="  United States District Court, District of New Hampshire  ",
        docket_locator="  Petition Vol. 12, Page 88  ",
        applicant_name_raw="  Patrick Murphy  ",
        event_date=event_dt,
        record_category="citizenship",
        record_type="petition_for_naturalization",
        court_location_id="LOC-000001",
        presiding_judge_or_clerk="Edgar Aldrich, Judge",
        volume_page="Vol. 12, p. 88",
        certificate_stub_number="Cert. 4189",
        stage="  petition  ",
        applicant_id="IND-000010",
        current_residence_raw="42 Main St, Concord, NH",
        current_residence_id="LOC-000001",
        date_of_birth=dob,
        place_of_birth_raw="County Cork, Ireland",
        place_of_birth_id="LOC-000020",
        country_of_prior_allegiance="Victoria, Queen of Great Britain and Ireland",
        port_of_entry_raw="New York, NY",
        arrival_date=arr_dt,
        vessel_name="S.S. Teutonic",
        witnesses=[w1, w2],
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.court_name == "United States District Court, District of New Hampshire"
    assert rec.docket_locator == "Petition Vol. 12, Page 88"
    assert rec.applicant_name_raw == "Patrick Murphy"
    assert rec.stage is NaturalizationStage.PETITION
    assert rec.court_location_id == LocationID("LOC-000001")
    assert rec.applicant_id == IndividualID("IND-000010")
    assert rec.current_residence_id == LocationID("LOC-000001")
    assert rec.place_of_birth_id == LocationID("LOC-000020")
    assert rec.witness_count == 2
    assert (
        str(rec)
        == "NaturalizationRecord [PETITION_FOR_NATURALIZATION] Patrick Murphy (Petition Vol. 12, Page 88)"
    )

    payload = rec.to_dict()
    assert payload["stage"] == "PETITION"
    assert len(payload["witnesses"]) == 2

    restored = NaturalizationRecord.from_dict(payload)
    assert restored == rec

    restored_json = NaturalizationRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct ArchivalURN, NaturalizationStage, AuditStamp, EventDate, and NaturalizationWitness instances
    direct_urn_rec = NaturalizationRecord.create(
        source_id=_SID,
        source_urn=ArchivalURN(_URN_NAT),
        description="Direct ArchivalURN and stage instance check.",
        repository_id="REP-000001",
        court_name="United States District Court, District of New Hampshire",
        docket_locator="Petition Vol. 12, Page 88",
        applicant_name_raw="Patrick Murphy",
        event_date=event_dt,
        stage=NaturalizationStage.OATH_OF_ALLEGIANCE,
    )
    assert direct_urn_rec.source_urn == ArchivalURN(_URN_NAT)
    assert direct_urn_rec.stage is NaturalizationStage.OATH_OF_ALLEGIANCE

    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["event_date"] = event_dt
    direct_payload["date_of_birth"] = dob
    direct_payload["arrival_date"] = arr_dt
    direct_payload["witnesses"] = [w1, w2]
    assert NaturalizationRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_naturalization_validation_and_minimal_roundtrip() -> None:
    """Verify NaturalizationRecord minimal round-trip and validation error branches."""
    minimal = NaturalizationRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_SRC,
        description="Declaration of Intention of Patrick Murphy.",
        repository_id=RepositoryID("REP-000001"),
        court_name="Merrimack County Superior Court",
        docket_locator="Declaration Book 4, p. 112",
        applicant_name_raw="Patrick Murphy",
        event_date="1895-04-02",
        record_category=SourceRecordCategory.LEGAL,
        record_type=SourceRecordType.DECLARATION_OF_INTENTION,
        media_ids=[MediaID(_MID)],
    )
    assert minimal.witness_count == 0
    min_dict = minimal.to_dict()
    for opt_key in (
        "court_location_id",
        "presiding_judge_or_clerk",
        "volume_page",
        "certificate_stub_number",
        "stage",
        "applicant_id",
        "current_residence_raw",
        "current_residence_id",
        "date_of_birth",
        "place_of_birth_raw",
        "place_of_birth_id",
        "country_of_prior_allegiance",
        "port_of_entry_raw",
        "arrival_date",
        "vessel_name",
    ):
        assert opt_key not in min_dict
    assert NaturalizationRecord.from_dict(min_dict) == minimal

    # Direct constructors trim whitespace
    direct_w = NaturalizationWitness(name="  John Kimball  ")
    assert direct_w.name == "John Kimball"

    direct_rec = NaturalizationRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        court_name="  Trimmed Court  ",
        docket_locator="  Trimmed Locator  ",
        applicant_name_raw="  Trimmed Applicant  ",
        event_date=minimal.event_date,
    )
    assert direct_rec.court_name == "Trimmed Court"
    assert direct_rec.docket_locator == "Trimmed Locator"
    assert direct_rec.applicant_name_raw == "Trimmed Applicant"

    # NaturalizationWitness error branches
    with pytest.raises(ModelFormatError, match="name"):
        NaturalizationWitness.create(name="   ")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        NaturalizationWitness.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'name'"):
        NaturalizationWitness.from_dict({})

    with pytest.raises(ModelFormatError, match="Failed to parse NaturalizationWitness JSON"):
        NaturalizationWitness.from_json("{bad-json")

    # NaturalizationRecord validation branches
    with pytest.raises(ModelFormatError, match="Invalid Naturalization URN syntax"):
        NaturalizationRecord.create(
            source_id=_SID,
            source_urn="URN:NATURALIZATION:bad",
            description="Bad URN",
            repository_id="REP-000001",
            court_name="Court",
            docket_locator="Loc",
            applicant_name_raw="Applicant",
            event_date="1895-04-02",
        )

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        NaturalizationRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong category",
            repository_id="REP-000001",
            court_name="Court",
            docket_locator="Loc",
            applicant_name_raw="Applicant",
            event_date="1895-04-02",
            record_category=SourceRecordCategory.VITAL,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        NaturalizationRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong type",
            repository_id="REP-000001",
            court_name="Court",
            docket_locator="Loc",
            applicant_name_raw="Applicant",
            event_date="1895-04-02",
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="court_name"):
        NaturalizationRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Empty court",
            repository_id="REP-000001",
            court_name="   ",
            docket_locator="Loc",
            applicant_name_raw="Applicant",
            event_date="1895-04-02",
        )

    with pytest.raises(ModelFormatError, match="Invalid NaturalizationStage value"):
        NaturalizationRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad stage",
            repository_id="REP-000001",
            court_name="Court",
            docket_locator="Loc",
            applicant_name_raw="Applicant",
            event_date="1895-04-02",
            stage="INVALID_STAGE",
        )

    with pytest.raises(ModelFormatError, match="Invalid 'event_date' payload"):
        NaturalizationRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad date",
            repository_id="REP-000001",
            court_name="Court",
            docket_locator="Loc",
            applicant_name_raw="Applicant",
            event_date=1895,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        NaturalizationRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        NaturalizationRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        NaturalizationRecord.from_dict(bad_audit)

    bad_witnesses = dict(min_dict)
    bad_witnesses["witnesses"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'witnesses' must be a list or tuple"):
        NaturalizationRecord.from_dict(bad_witnesses)
