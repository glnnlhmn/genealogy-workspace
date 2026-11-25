"""Path: tests/test_gda/test_model/test_source/test_vital/test_vital_marriage.py

Comprehensive unit tests for gda.model.source.vital.marriage.MarriageRecord.

Operational Role:
    Exercises factory creation, SourceRecord inheritance, VITAL/CHURCH category
    bounds, Age and EventDate coercion, dict/JSON round-trip serialization,
    and defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import MaritalStatus, UnionDissolutionType, UnionType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import VitalCertificateUrn
from gda.model.base.age import Age
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.vital import MarriageRecord

__version__ = "1.0.0+build.4"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN = "URN:VITAL:MARRIAGE:1894:US_NH_CONCORD:LIC_042"
_URN_MIN = "URN:SRC:1894:US_NH_CONCORD:CHURCH_MAR_09"


@pytest.mark.unit
@pytest.mark.smoke
def test_marriage_record_create_and_roundtrip() -> None:
    """Verify MarriageRecord.create with full spouse details, ages, and serialization."""
    now = IsoTimestamp("2026-05-02T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    issued = EventDate.create("1894-06-10")
    dom = EventDate.create("1894-06-14")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000003"),
        name_raw="Rev. Nathan F. Carter",
        role=AssociatedRole.OFFICIANT,
    )

    rec = MarriageRecord.create(
        source_id=_SID,
        source_urn=VitalCertificateUrn(_URN),
        description="Marriage License and Return of John H. Abbott and Mary E. Colby.",
        repository_id="REP-000001",
        groom_name_raw=" John H. Abbott ",
        bride_name_raw=" Mary E. Colby ",
        record_category="vital",
        record_type="marriage_license",
        union_type="married",
        license_number="MC-1894-042",
        date_issued=issued,
        issuing_jurisdiction_raw="Concord City Clerk, Merrimack County, NH",
        groom_id="IND-000001",
        groom_age=Age(raw_text="27 years, 3 months", years=27, months=3, days=4),
        groom_marital_status="single",
        groom_prior_dissolution="unknown",
        groom_residence_raw="Concord, NH",
        bride_id="IND-000002",
        bride_maiden_name_raw="Colby",
        bride_age=24,
        bride_marital_status="widowed",
        bride_prior_dissolution="death",
        bride_residence_raw="Bow, NH",
        date_of_marriage=dom,
        place_of_marriage_raw="First Congregational Church, Concord, NH",
        place_of_marriage_id="LOC-000001",
        officiant_name_raw="Nathan F. Carter",
        officiant_title_raw="Clergyman",
        religious_denomination="Congregational",
        witnesses=["George W. Abbott", "Sarah J. Colby"],
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.groom_name_raw == "John H. Abbott"
    assert rec.bride_name_raw == "Mary E. Colby"
    assert rec.union_type is UnionType.MARRIED
    assert rec.groom_age == Age(raw_text="27 years, 3 months", years=27, months=3, days=4)
    assert rec.bride_age == Age(years=24)
    assert rec.groom_marital_status is MaritalStatus.SINGLE
    assert rec.bride_marital_status is MaritalStatus.WIDOWED
    assert rec.groom_prior_dissolution is UnionDissolutionType.UNKNOWN
    assert rec.bride_prior_dissolution is UnionDissolutionType.DEATH
    assert str(rec) == "MarriageRecord [John H. Abbott & Mary E. Colby]"

    payload = rec.to_dict()
    assert payload["license_number"] == "MC-1894-042"
    assert payload["groom_age"] == {
        "raw_text": "27 years, 3 months",
        "years": 27,
        "months": 3,
        "days": 4,
    }
    assert payload["bride_age"] == {"years": 24}

    restored = MarriageRecord.from_dict(payload)
    assert restored == rec

    restored_json = MarriageRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct AuditStamp, EventDate, Age, and string age in from_dict + text-only Age serialization
    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["date_issued"] = issued
    direct_payload["date_of_marriage"] = dom
    direct_payload["groom_age"] = Age(years=27)
    direct_payload["bride_age"] = "24y"
    restored_direct = MarriageRecord.from_dict(direct_payload)
    assert restored_direct.groom_age == Age(years=27)
    assert restored_direct.bride_age == Age(raw_text="24y")
    assert restored_direct.to_dict()["bride_age"] == {"raw_text": "24y"}


@pytest.mark.unit
@pytest.mark.integrity
def test_marriage_record_validation_and_minimal_roundtrip() -> None:
    """Verify MarriageRecord minimal round-trip and validation boundaries."""
    minimal = MarriageRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_MIN,
        description="Parish Marriage Register Entry.",
        repository_id=RepositoryID("REP-000001"),
        groom_name_raw="Thomas Bean",
        bride_name_raw="Esther Kimball",
        record_category=SourceRecordCategory.CHURCH,
        record_type=SourceRecordType.MARRIAGE_REGISTER,
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "license_number",
        "date_issued",
        "issuing_jurisdiction_raw",
        "groom_id",
        "groom_age",
        "groom_marital_status",
        "groom_prior_dissolution",
        "groom_residence_raw",
        "bride_id",
        "bride_maiden_name_raw",
        "bride_age",
        "bride_marital_status",
        "bride_prior_dissolution",
        "bride_residence_raw",
        "date_of_marriage",
        "place_of_marriage_raw",
        "place_of_marriage_id",
        "officiant_name_raw",
        "officiant_title_raw",
        "religious_denomination",
    ):
        assert opt_key not in min_dict
    assert MarriageRecord.from_dict(min_dict) == minimal

    # Direct constructor trims groom_name_raw and bride_name_raw
    direct = MarriageRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        groom_name_raw=" Trimmed Groom ",
        bride_name_raw=" Trimmed Bride ",
    )
    assert direct.groom_name_raw == "Trimmed Groom"
    assert direct.bride_name_raw == "Trimmed Bride"

    # Disallowed category / record_type
    with pytest.raises(ModelFormatError, match="requires record_category in"):
        MarriageRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong category",
            repository_id="REP-000001",
            groom_name_raw="Thomas Bean",
            bride_name_raw="Esther Kimball",
            record_category=SourceRecordCategory.TAX,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        MarriageRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong type",
            repository_id="REP-000001",
            groom_name_raw="Thomas Bean",
            bride_name_raw="Esther Kimball",
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    # Empty groom / bride / bad date / bad age
    with pytest.raises(ModelFormatError, match="groom_name_raw"):
        MarriageRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty groom",
            repository_id="REP-000001",
            groom_name_raw="   ",
            bride_name_raw="Esther Kimball",
        )

    with pytest.raises(ModelFormatError, match="bride_name_raw"):
        MarriageRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty bride",
            repository_id="REP-000001",
            groom_name_raw="Thomas Bean",
            bride_name_raw="   ",
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_of_marriage' payload"):
        MarriageRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad date",
            repository_id="REP-000001",
            groom_name_raw="Thomas Bean",
            bride_name_raw="Esther Kimball",
            date_of_marriage=1894,  # type: ignore[arg-type]
        )

    with pytest.raises(ModelFormatError, match="Invalid 'groom_age' payload"):
        MarriageRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad age",
            repository_id="REP-000001",
            groom_name_raw="Thomas Bean",
            bride_name_raw="Esther Kimball",
            groom_age=True,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        MarriageRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        MarriageRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = "bad"
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        MarriageRecord.from_dict(bad_audit)
