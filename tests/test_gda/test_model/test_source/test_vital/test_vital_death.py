"""Path: tests/test_gda/test_model/test_source/test_vital/test_vital_death.py

Comprehensive unit tests for gda.model.source.vital.death.DeathRecord.

Operational Role:
    Exercises factory creation, SourceRecord inheritance, VITAL category bounds,
    medical/disposition fields, Age and EventDate coercion, dict/JSON round-trip
    serialization, and defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole, Sex
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import DispositionType, MannerOfDeath, MaritalStatus
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, MediaID, RepositoryID, SiteID, SourceID
from gda.model.atom.urn import VitalCertificateUrn
from gda.model.base.age import Age
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.vital import DeathRecord

__version__ = "1.0.0+build.3"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN = "URN:VITAL:DEATH:1942:US_NH_CONCORD:CERT_819"
_URN_MIN = "URN:SRC:1943:US_NH_CONCORD:DEATH_REG_22"


@pytest.mark.unit
@pytest.mark.smoke
def test_death_record_create_and_roundtrip() -> None:
    """Verify DeathRecord.create with full medical/disposition fields and serialization."""
    now = IsoTimestamp("2026-05-03T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    dob = EventDate.create("1867-02-10")
    dod = EventDate.create("1942-11-19")
    disp_date = EventDate.create("1942-11-22")
    filed = EventDate.create("1942-11-20")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000004"),
        name_raw="Samuel H. Abbott",
        role=AssociatedRole.INFORMANT,
    )

    rec = DeathRecord.create(
        source_id=_SID,
        source_urn=VitalCertificateUrn(_URN),
        description="Death Certificate of John H. Abbott, Concord, NH.",
        repository_id="REP-000001",
        decedent_name_raw="  John H. Abbott  ",
        date_of_death=dod,
        place_of_death_raw="  Margaret Pillsbury General Hospital, Concord, NH  ",
        record_type="death_certificate",
        decedent_id="IND-000001",
        sex="M",
        is_stillborn=False,
        marital_status="married",
        spouse_name_raw="Mary E. Colby",
        date_of_birth=dob,
        age_at_death=Age(raw_text="75 years, 9 months, 9 days", years=75, months=9, days=9),
        time_of_death="11:15 PM",
        place_of_death_id="LOC-000001",
        residence_raw="42 Main St., Concord, NH",
        occupation_raw="Master Carpenter",
        father_name_raw="George W. Abbott",
        mother_maiden_name_raw="Hannah Kimball",
        manner_of_death="natural",
        cause_of_death_raw="Chronic Myocarditis; Arteriosclerosis",
        attending_physician_raw="Dr. Charles R. Walker",
        informant_name_raw="Samuel H. Abbott",
        disposition_type="burial",
        disposition_date=disp_date,
        disposition_place_raw="Blossom Hill Cemetery, Concord, NH",
        disposition_site_id="SID-000001",
        undertaker_raw="Waters Funeral Home",
        certificate_number="NH-1942-0819",
        date_filed=filed,
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.decedent_name_raw == "John H. Abbott"
    assert rec.place_of_death_raw == "Margaret Pillsbury General Hospital, Concord, NH"
    assert rec.decedent_id == IndividualID("IND-000001")
    assert rec.sex is Sex.MALE
    assert rec.marital_status is MaritalStatus.MARRIED
    assert rec.manner_of_death is MannerOfDeath.NATURAL
    assert rec.disposition_type is DispositionType.BURIAL
    assert rec.disposition_site_id == SiteID("SID-000001")
    assert str(rec) == "DeathRecord [John H. Abbott] (1942-11-19)"

    payload = rec.to_dict()
    assert payload["decedent_id"] == "IND-000001"
    assert payload["age_at_death"] == {
        "raw_text": "75 years, 9 months, 9 days",
        "years": 75,
        "months": 9,
        "days": 9,
    }
    assert payload["disposition_site_id"] == "SID-000001"

    restored = DeathRecord.from_dict(payload)
    assert restored == rec

    restored_json = DeathRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct AuditStamp, EventDate, Age, int age, and string age in from_dict + partial Age serialization
    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["date_of_death"] = dod
    direct_payload["date_of_birth"] = dob
    direct_payload["disposition_date"] = disp_date
    direct_payload["date_filed"] = filed
    direct_payload["age_at_death"] = Age(years=75)
    restored_direct = DeathRecord.from_dict(direct_payload)
    assert restored_direct.age_at_death == Age(years=75)
    assert restored_direct.to_dict()["age_at_death"] == {"years": 75}

    int_age_payload = dict(payload)
    int_age_payload["age_at_death"] = 75
    assert DeathRecord.from_dict(int_age_payload).age_at_death == Age(years=75)

    str_age_payload = dict(payload)
    str_age_payload["age_at_death"] = "75y"
    restored_str_age = DeathRecord.from_dict(str_age_payload)
    assert restored_str_age.age_at_death == Age(raw_text="75y")
    assert restored_str_age.to_dict()["age_at_death"] == {"raw_text": "75y"}


@pytest.mark.unit
@pytest.mark.integrity
def test_death_record_validation_and_minimal_roundtrip() -> None:
    """Verify DeathRecord minimal round-trip and validation error branches."""
    minimal = DeathRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_MIN,
        description="Town Death Register Entry.",
        repository_id=RepositoryID("REP-000001"),
        decedent_name_raw="Mary E. Abbott",
        date_of_death="1943-01-12",
        place_of_death_raw="Concord, NH",
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "decedent_id",
        "marital_status",
        "spouse_name_raw",
        "date_of_birth",
        "age_at_death",
        "time_of_death",
        "place_of_death_id",
        "residence_raw",
        "occupation_raw",
        "father_name_raw",
        "mother_maiden_name_raw",
        "manner_of_death",
        "cause_of_death_raw",
        "attending_physician_raw",
        "informant_name_raw",
        "disposition_type",
        "disposition_date",
        "disposition_place_raw",
        "disposition_site_id",
        "undertaker_raw",
        "certificate_number",
        "date_filed",
    ):
        assert opt_key not in min_dict
    assert DeathRecord.from_dict(min_dict) == minimal

    # Direct constructor trims decedent_name_raw and place_of_death_raw
    direct = DeathRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        decedent_name_raw="  Trimmed Decedent  ",
        date_of_death=EventDate.create("1943-01-12"),
        place_of_death_raw="  Trimmed Place  ",
    )
    assert direct.decedent_name_raw == "Trimmed Decedent"
    assert direct.place_of_death_raw == "Trimmed Place"

    # Disallowed category / record_type
    with pytest.raises(ModelFormatError, match="requires record_category VITAL"):
        DeathRecord(
            source_id=SourceID(_SID),
            source_urn=minimal.source_urn,
            record_category=SourceRecordCategory.CHURCH,
            description="Wrong category",
            repository_id=RepositoryID("REP-000001"),
            audit=minimal.audit,
            decedent_name_raw="Mary E. Abbott",
            date_of_death=EventDate.create("1943-01-12"),
            place_of_death_raw="Concord, NH",
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        DeathRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong type",
            repository_id="REP-000001",
            decedent_name_raw="Mary E. Abbott",
            date_of_death="1943-01-12",
            place_of_death_raw="Concord, NH",
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    # Empty decedent / empty place / bad date / bad age
    with pytest.raises(ModelFormatError, match="decedent_name_raw"):
        DeathRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty decedent",
            repository_id="REP-000001",
            decedent_name_raw="   ",
            date_of_death="1943-01-12",
            place_of_death_raw="Concord, NH",
        )

    with pytest.raises(ModelFormatError, match="place_of_death_raw"):
        DeathRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty place",
            repository_id="REP-000001",
            decedent_name_raw="Mary E. Abbott",
            date_of_death="1943-01-12",
            place_of_death_raw="   ",
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_of_death' payload"):
        DeathRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad date",
            repository_id="REP-000001",
            decedent_name_raw="Mary E. Abbott",
            date_of_death=19430112,  # type: ignore[arg-type]
            place_of_death_raw="Concord, NH",
        )

    with pytest.raises(ModelFormatError, match="Invalid 'age_at_death' payload"):
        DeathRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad age",
            repository_id="REP-000001",
            decedent_name_raw="Mary E. Abbott",
            date_of_death="1943-01-12",
            place_of_death_raw="Concord, NH",
            age_at_death=False,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        DeathRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        DeathRecord.from_dict({"source_id": _SID})

    wrong_cat = dict(min_dict)
    wrong_cat["record_category"] = "LEGAL"
    with pytest.raises(ModelFormatError, match="requires record_category VITAL"):
        DeathRecord.from_dict(wrong_cat)

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 999
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        DeathRecord.from_dict(bad_audit)
