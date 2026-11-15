"""Path: tests/test_gda/test_model/test_source/test_vital/test_vital_birth.py

Comprehensive unit tests for gda.model.source.vital.birth.BirthRecord.

Operational Role:
    Exercises factory creation, SourceRecord inheritance, category and record_type
    bounds, EventDate coercion, dict/JSON round-trip serialization, and defensive
    deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole, Sex
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import BirthPlurality, VitalModifier
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import VitalCertificateUrn
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.vital import BirthRecord

__version__ = "1.0.0+build.2"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN = "URN:VITAL:BIRTH:1895:US_NH_CONCORD:CERT_104"
_URN_MIN = "URN:SRC:1896:US_NH_CONCORD:BIRTH_REG_12"


@pytest.mark.unit
@pytest.mark.smoke
def test_birth_record_create_and_roundtrip() -> None:
    """Verify BirthRecord.create with full metadata, properties, and dict/JSON serialization."""
    now = IsoTimestamp("2026-05-01T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    dob = EventDate.create("1895-04-12")
    filed = EventDate.create("1895-04-15")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000002"),
        name_raw="Dr. Arthur W. Hill",
        role=AssociatedRole.PHYSICIAN,
    )

    rec = BirthRecord.create(
        source_id=_SID,
        source_urn=VitalCertificateUrn(_URN),
        description="Civil Birth Certificate of Samuel H. Abbott, Concord, NH.",
        repository_id="REP-000001",
        child_name_raw="  Samuel H. Abbott  ",
        date_of_birth=dob,
        place_of_birth_raw="  Concord, Merrimack County, NH  ",
        record_type="birth_certificate",
        child_id="IND-000001",
        sex="M",
        plurality="twin",
        birth_order="1st of Twins (2nd child)",
        is_stillborn=False,
        vital_modifier="posthumous",
        time_of_birth="04:30 AM",
        place_of_birth_id="LOC-000001",
        legitimacy=True,
        certificate_number="NH-1895-0104",
        registration_district="Concord Ward 4",
        date_filed=filed,
        father_name_raw="John H. Abbott",
        mother_maiden_name_raw="Mary E. Colby",
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.source_id == SourceID(_SID)
    assert rec.record_category is SourceRecordCategory.VITAL
    assert rec.record_type is SourceRecordType.BIRTH_CERTIFICATE
    assert rec.child_name_raw == "Samuel H. Abbott"
    assert rec.place_of_birth_raw == "Concord, Merrimack County, NH"
    assert rec.child_id == IndividualID("IND-000001")
    assert rec.sex is Sex.MALE
    assert rec.plurality is BirthPlurality.TWIN
    assert rec.vital_modifier is VitalModifier.POSTHUMOUS
    assert rec.place_of_birth_id == LocationID("LOC-000001")
    assert rec.date_filed == filed
    assert str(rec) == "BirthRecord [Samuel H. Abbott] (1895-04-12)"

    payload = rec.to_dict()
    assert payload["child_id"] == "IND-000001"
    assert payload["birth_order"] == "1st of Twins (2nd child)"
    assert payload["vital_modifier"] == "POSTHUMOUS"
    assert payload["time_of_birth"] == "04:30 AM"
    assert payload["place_of_birth_id"] == "LOC-000001"
    assert payload["legitimacy"] is True
    assert payload["certificate_number"] == "NH-1895-0104"
    assert payload["registration_district"] == "Concord Ward 4"
    assert payload["date_filed"] == filed.to_dict()
    assert payload["father_name_raw"] == "John H. Abbott"
    assert payload["mother_maiden_name_raw"] == "Mary E. Colby"

    restored = BirthRecord.from_dict(payload)
    assert restored == rec

    restored_json = BirthRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct AuditStamp and EventDate objects passed in from_dict
    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["date_of_birth"] = dob
    direct_payload["date_filed"] = filed
    assert BirthRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_birth_record_validation_and_minimal_roundtrip() -> None:
    """Verify BirthRecord minimal round-trip and validation error branches."""
    minimal = BirthRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_MIN,
        description="Town Birth Register Entry for Hannah Colby.",
        repository_id=RepositoryID("REP-000001"),
        child_name_raw="Hannah Colby",
        date_of_birth="1896-08-03",
        place_of_birth_raw="Bow, NH",
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "child_id",
        "birth_order",
        "vital_modifier",
        "time_of_birth",
        "place_of_birth_id",
        "legitimacy",
        "certificate_number",
        "registration_district",
        "date_filed",
        "father_name_raw",
        "mother_maiden_name_raw",
    ):
        assert opt_key not in min_dict
    assert BirthRecord.from_dict(min_dict) == minimal

    # Direct constructor trims child_name_raw and place_of_birth_raw
    direct = BirthRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct init test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        child_name_raw="  Trimmed Child  ",
        date_of_birth=EventDate.create("1896-08-03"),
        place_of_birth_raw="  Trimmed Place  ",
    )
    assert direct.child_name_raw == "Trimmed Child"
    assert direct.place_of_birth_raw == "Trimmed Place"

    # Disallowed record_category in __post_init__
    with pytest.raises(ModelFormatError, match="requires record_category VITAL"):
        BirthRecord(
            source_id=SourceID(_SID),
            source_urn=minimal.source_urn,
            record_category=SourceRecordCategory.CHURCH,
            description="Wrong category",
            repository_id=RepositoryID("REP-000001"),
            audit=minimal.audit,
            child_name_raw="Hannah Colby",
            date_of_birth=EventDate.create("1896-08-03"),
            place_of_birth_raw="Bow, NH",
        )

    # Disallowed record_type
    with pytest.raises(ModelFormatError, match="requires record_type in"):
        BirthRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong type",
            repository_id="REP-000001",
            child_name_raw="Hannah Colby",
            date_of_birth="1896-08-03",
            place_of_birth_raw="Bow, NH",
            record_type=SourceRecordType.DEATH_CERTIFICATE,
        )

    # Empty child_name_raw / place_of_birth_raw / invalid date_of_birth type
    with pytest.raises(ModelFormatError, match="child_name_raw"):
        BirthRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty child",
            repository_id="REP-000001",
            child_name_raw="   ",
            date_of_birth="1896-08-03",
            place_of_birth_raw="Bow, NH",
        )

    with pytest.raises(ModelFormatError, match="place_of_birth_raw"):
        BirthRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty place",
            repository_id="REP-000001",
            child_name_raw="Hannah Colby",
            date_of_birth="1896-08-03",
            place_of_birth_raw="   ",
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_of_birth' payload"):
        BirthRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad date type",
            repository_id="REP-000001",
            child_name_raw="Hannah Colby",
            date_of_birth=18960803,  # type: ignore[arg-type]
            place_of_birth_raw="Bow, NH",
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        BirthRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        BirthRecord.from_dict({"source_id": _SID})

    wrong_cat = dict(min_dict)
    wrong_cat["record_category"] = "CHURCH"
    with pytest.raises(ModelFormatError, match="requires record_category VITAL"):
        BirthRecord.from_dict(wrong_cat)

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        BirthRecord.from_dict(bad_audit)
