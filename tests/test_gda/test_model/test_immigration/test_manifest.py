"""Path: tests/test_gda/test_model/test_immigration/test_manifest.py

Comprehensive unit tests for gda.model.immigration.manifest
(ImmigrationManifestRecord and ManifestPassenger).

Operational Role:
    Exercises ManifestPassenger and ImmigrationManifestRecord creation,
    URN:IMMIGRATION and URN:SRC resolution, ArrivalPassageClass, Sex, and
    MaritalStatus enum parsing, flatten_passengers() tabular projection,
    dict/JSON round-trip serialization, and defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole, Sex
from gda.core.enums.immigration import ArrivalPassageClass
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import MaritalStatus
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.immigration import ImmigrationManifestRecord, ManifestPassenger

__version__ = "1.0.0+build.1"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN_IMM = "URN:IMMIGRATION:1892:US_NY_ELLIS:M237_R598_L14"
_URN_SRC = "URN:SRC:1911:US_VT_STALBANS:BORDER_CARD_402"


@pytest.mark.unit
@pytest.mark.smoke
def test_manifest_passenger_and_record_roundtrip() -> None:
    """Verify ManifestPassenger and ImmigrationManifestRecord full metadata and serialization."""
    now = IsoTimestamp("2026-10-01T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
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

    p1 = ManifestPassenger.create(
        full_name="  Patrick Murphy  ",
        line_number=14,
        individual_id="IND-000010",
        age_raw="27",
        sex="Male",
        marital_status="Single",
        occupation="Laborer",
        passage_class="  steerage  ",
        nationality_or_race_raw="Irish",
        last_permanent_residence_raw="Queenstown, Ireland",
        last_permanent_residence_id="LOC-000020",
        final_destination_raw="Concord, NH",
        final_destination_id="LOC-000001",
        relative_joined_name="Michael Murphy",
        relative_joined_relationship="Brother",
        relative_joined_address="42 Main St, Concord, NH",
    )
    p2 = ManifestPassenger.create(
        full_name="Bridget Murphy",
        sex=Sex.FEMALE,
        marital_status=MaritalStatus.SINGLE,
        passage_class=ArrivalPassageClass.STEERAGE,
    )

    assert p1.full_name == "Patrick Murphy"
    assert p1.sex is Sex.MALE
    assert p1.marital_status is MaritalStatus.SINGLE
    assert p1.passage_class is ArrivalPassageClass.STEERAGE
    assert str(p1) == "Line 14: Patrick Murphy"
    assert str(p2) == "Bridget Murphy"
    assert ManifestPassenger.from_json(p1.to_json()) == p1

    p2_dict = p2.to_dict()
    for opt_key in (
        "line_number",
        "individual_id",
        "age_raw",
        "occupation",
        "nationality_or_race_raw",
        "last_permanent_residence_raw",
        "last_permanent_residence_id",
        "final_destination_raw",
        "final_destination_id",
        "relative_joined_name",
        "relative_joined_relationship",
        "relative_joined_address",
    ):
        assert opt_key not in p2_dict
    assert ManifestPassenger.from_dict(p2_dict) == p2

    rec = ImmigrationManifestRecord.create(
        source_id=_SID,
        source_urn=_URN_IMM,
        description="Passenger Arrival Manifest for S.S. Teutonic at New York.",
        repository_id="REP-000001",
        port_of_arrival_raw="  New York, NY  ",
        arrival_date=arr_dt,
        manifest_locator="  NARA M237 Roll 598, List 14  ",
        passengers=[p1, p2],
        record_category="immigration",
        record_type="passenger_manifest",
        port_of_arrival_id="LOC-000030",
        ship_name="S.S. Teutonic",
        master_or_captain="Capt. J. G. Cameron",
        shipping_line="White Star Line",
        port_of_departure_raw="Liverpool & Queenstown",
        port_of_departure_id="LOC-000031",
        list_number="List 14",
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.port_of_arrival_raw == "New York, NY"
    assert rec.manifest_locator == "NARA M237 Roll 598, List 14"
    assert rec.port_of_arrival_id == LocationID("LOC-000030")
    assert rec.port_of_departure_id == LocationID("LOC-000031")
    assert rec.passenger_count == 2
    assert (
        str(rec)
        == "ImmigrationManifestRecord [PASSENGER_MANIFEST] New York, NY on S.S. Teutonic (NARA M237 Roll 598, List 14)"
    )

    flat = rec.flatten_passengers()
    assert len(flat) == 2
    assert flat[0]["full_name"] == "Patrick Murphy"
    assert flat[0]["ship_name"] == "S.S. Teutonic"
    assert flat[1]["full_name"] == "Bridget Murphy"

    payload = rec.to_dict()
    assert payload["ship_name"] == "S.S. Teutonic"
    assert len(payload["passengers"]) == 2

    restored = ImmigrationManifestRecord.from_dict(payload)
    assert restored == rec

    restored_json = ImmigrationManifestRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct ArchivalURN, AuditStamp, EventDate, and ManifestPassenger instances
    direct_urn_rec = ImmigrationManifestRecord.create(
        source_id=_SID,
        source_urn=ArchivalURN(_URN_IMM),
        description="Direct ArchivalURN instance check.",
        repository_id="REP-000001",
        port_of_arrival_raw="New York, NY",
        arrival_date=arr_dt,
        manifest_locator="NARA M237 Roll 598, List 14",
        passengers=[p1],
    )
    assert direct_urn_rec.source_urn == ArchivalURN(_URN_IMM)

    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["arrival_date"] = arr_dt
    direct_payload["passengers"] = [p1, p2]
    assert ImmigrationManifestRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_manifest_validation_and_minimal_roundtrip() -> None:
    """Verify ImmigrationManifestRecord minimal round-trip and validation error branches."""
    minimal = ImmigrationManifestRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_SRC,
        description="St. Albans Border Crossing Card for Jean Baptiste Roy.",
        repository_id=RepositoryID("REP-000001"),
        port_of_arrival_raw="St. Albans, VT",
        arrival_date="1911-05-04",
        manifest_locator="NARA M1464 Roll 152",
        passengers=[{"full_name": "Jean Baptiste Roy"}],
        record_category=SourceRecordCategory.TRAVEL,
        record_type=SourceRecordType.BORDER_CROSSING_CARD,
        media_ids=[MediaID(_MID)],
    )
    assert str(minimal) == (
        "ImmigrationManifestRecord [BORDER_CROSSING_CARD] St. Albans, VT (NARA M1464 Roll 152)"
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "port_of_arrival_id",
        "ship_name",
        "master_or_captain",
        "shipping_line",
        "port_of_departure_raw",
        "port_of_departure_id",
        "list_number",
    ):
        assert opt_key not in min_dict
    assert ImmigrationManifestRecord.from_dict(min_dict) == minimal

    # Direct constructors normalize whitespace and guard empty passengers
    direct_p = ManifestPassenger(full_name="  Marie Roy  ")
    assert direct_p.full_name == "Marie Roy"

    direct_rec = ImmigrationManifestRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        port_of_arrival_raw="  Trimmed Port  ",
        arrival_date=minimal.arrival_date,
        manifest_locator="  Trimmed Locator  ",
        passengers=minimal.passengers,
    )
    assert direct_rec.port_of_arrival_raw == "Trimmed Port"
    assert direct_rec.manifest_locator == "Trimmed Locator"

    with pytest.raises(ModelFormatError, match="requires at least one ManifestPassenger"):
        ImmigrationManifestRecord(
            source_id=SourceID(_SID),
            source_urn=minimal.source_urn,
            description="Empty passengers",
            repository_id=RepositoryID("REP-000001"),
            audit=minimal.audit,
            port_of_arrival_raw="Port",
            arrival_date=minimal.arrival_date,
            manifest_locator="Loc",
            passengers=(),
        )

    # ManifestPassenger error branches
    with pytest.raises(ModelFormatError, match="full_name"):
        ManifestPassenger.create(full_name="   ")

    with pytest.raises(ModelFormatError, match="Invalid Sex value"):
        ManifestPassenger.create(full_name="Test", sex="INVALID_SEX")

    with pytest.raises(ModelFormatError, match="Invalid ArrivalPassageClass value"):
        ManifestPassenger.create(full_name="Test", passage_class="FIRST_CLASS_SUITE")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        ManifestPassenger.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'full_name'"):
        ManifestPassenger.from_dict({})

    with pytest.raises(ModelFormatError, match="Failed to parse ManifestPassenger JSON"):
        ManifestPassenger.from_json("{bad-json")

    # ImmigrationManifestRecord validation branches
    with pytest.raises(ModelFormatError, match="Invalid Immigration URN syntax"):
        ImmigrationManifestRecord.create(
            source_id=_SID,
            source_urn="URN:IMMIGRATION:bad",
            description="Bad URN",
            repository_id="REP-000001",
            port_of_arrival_raw="Port",
            arrival_date="1911-05-04",
            manifest_locator="Loc",
            passengers=[{"full_name": "A"}],
        )

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        ImmigrationManifestRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong category",
            repository_id="REP-000001",
            port_of_arrival_raw="Port",
            arrival_date="1911-05-04",
            manifest_locator="Loc",
            passengers=[{"full_name": "A"}],
            record_category=SourceRecordCategory.CENSUS,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        ImmigrationManifestRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong type",
            repository_id="REP-000001",
            port_of_arrival_raw="Port",
            arrival_date="1911-05-04",
            manifest_locator="Loc",
            passengers=[{"full_name": "A"}],
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="port_of_arrival_raw"):
        ImmigrationManifestRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Empty port",
            repository_id="REP-000001",
            port_of_arrival_raw="   ",
            arrival_date="1911-05-04",
            manifest_locator="Loc",
            passengers=[{"full_name": "A"}],
        )

    with pytest.raises(ModelFormatError, match="Invalid 'arrival_date' payload"):
        ImmigrationManifestRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad date",
            repository_id="REP-000001",
            port_of_arrival_raw="Port",
            arrival_date=1911,  # type: ignore[arg-type]
            manifest_locator="Loc",
            passengers=[{"full_name": "A"}],
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        ImmigrationManifestRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        ImmigrationManifestRecord.from_dict({"source_id": _SID})

    bad_passengers = dict(min_dict)
    bad_passengers["passengers"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'passengers' must be a list or tuple"):
        ImmigrationManifestRecord.from_dict(bad_passengers)

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        ImmigrationManifestRecord.from_dict(bad_audit)
