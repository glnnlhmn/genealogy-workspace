"""Path: tests/test_gda/test_model/test_source/test_vital/test_vital_baptism.py

Comprehensive unit tests for gda.model.source.vital.baptism.BaptismRecord.

Operational Role:
    Exercises factory creation, SourceRecord inheritance, CHURCH/VITAL category
    bounds, EventDate coercion, dict/JSON round-trip serialization, and defensive
    deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole, Sex
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    MediaID,
    OrganizationID,
    RepositoryID,
    SiteID,
    SourceID,
)
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.vital import BaptismRecord

__version__ = "1.0.0+build.2"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN = "URN:SRC:1872:US_NH_CONCORD:BAP_VOL2_P18"
_URN_MIN = "URN:SRC:1873:US_NH_CONCORD:BAP_VOL2_P19"


@pytest.mark.unit
@pytest.mark.smoke
def test_baptism_record_create_and_roundtrip() -> None:
    """Verify BaptismRecord.create with full parish register details and serialization."""
    now = IsoTimestamp("2026-05-05T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    dob = EventDate.create("1872-03-01")
    bap_date = EventDate.create("1872-06-09")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000006"),
        name_raw="Elizabeth Colby",
        role=AssociatedRole.GODPARENT,
    )

    rec = BaptismRecord.create(
        source_id=_SID,
        source_urn=_URN,
        description="Baptism of Grace E. Abbott at St. Paul's Episcopal Church.",
        repository_id="REP-000001",
        church_name_raw="  St. Paul's Episcopal Church  ",
        baptized_name_raw="  Grace E. Abbott  ",
        date_of_baptism=bap_date,
        record_category="church",
        record_type="baptism_register",
        church_org_id="ORG-000015",
        church_site_id="SID-000003",
        location_id="LOC-000001",
        denomination="Episcopal",
        volume_title="Parish Register Vol. II (1865-1885)",
        register_locator="Page 18, Entry 4",
        individual_id="IND-000007",
        sex="F",
        date_of_birth=dob,
        place_of_birth_raw="Concord, NH",
        officiant_name_raw="Rev. James H. Eames",
        father_name_raw="John H. Abbott",
        mother_name_raw="Mary E. Colby",
        sponsors_or_godparents=["Elizabeth Colby", "Henry A. Kimball"],
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.church_name_raw == "St. Paul's Episcopal Church"
    assert rec.baptized_name_raw == "Grace E. Abbott"
    assert rec.church_org_id == OrganizationID("ORG-000015")
    assert rec.church_site_id == SiteID("SID-000003")
    assert rec.location_id == LocationID("LOC-000001")
    assert rec.individual_id == IndividualID("IND-000007")
    assert rec.sex is Sex.FEMALE
    assert rec.sponsors_or_godparents == ["Elizabeth Colby", "Henry A. Kimball"]
    assert str(rec) == "BaptismRecord [Grace E. Abbott @ St. Paul's Episcopal Church] (1872-06-09)"

    payload = rec.to_dict()
    assert payload["church_org_id"] == "ORG-000015"
    assert payload["church_site_id"] == "SID-000003"
    assert payload["denomination"] == "Episcopal"
    assert payload["volume_title"] == "Parish Register Vol. II (1865-1885)"
    assert payload["register_locator"] == "Page 18, Entry 4"

    restored = BaptismRecord.from_dict(payload)
    assert restored == rec

    restored_json = BaptismRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct AuditStamp and EventDate objects passed in from_dict
    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["date_of_baptism"] = bap_date
    direct_payload["date_of_birth"] = dob
    assert BaptismRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_baptism_record_validation_and_minimal_roundtrip() -> None:
    """Verify BaptismRecord minimal round-trip and validation error branches."""
    minimal = BaptismRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_MIN,
        description="Cradle Roll Entry.",
        repository_id=RepositoryID("REP-000001"),
        church_name_raw="First Congregational Church",
        baptized_name_raw="Arthur W. Colby",
        date_of_baptism="1873-05-11",
        record_category=SourceRecordCategory.VITAL,
        record_type=SourceRecordType.CRADLE_ROLL,
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "church_org_id",
        "church_site_id",
        "location_id",
        "denomination",
        "volume_title",
        "register_locator",
        "individual_id",
        "sex",
        "date_of_birth",
        "place_of_birth_raw",
        "officiant_name_raw",
        "father_name_raw",
        "mother_name_raw",
    ):
        assert opt_key not in min_dict
    assert BaptismRecord.from_dict(min_dict) == minimal

    # Direct constructor trims church_name_raw and baptized_name_raw
    direct = BaptismRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        church_name_raw="  Trimmed Church  ",
        baptized_name_raw="  Trimmed Infant  ",
        date_of_baptism=EventDate.create("1873-05-11"),
    )
    assert direct.church_name_raw == "Trimmed Church"
    assert direct.baptized_name_raw == "Trimmed Infant"

    # Disallowed category / record_type
    with pytest.raises(ModelFormatError, match="requires record_category in"):
        BaptismRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong category",
            repository_id="REP-000001",
            church_name_raw="First Congregational Church",
            baptized_name_raw="Arthur W. Colby",
            date_of_baptism="1873-05-11",
            record_category=SourceRecordCategory.MILITARY,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        BaptismRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong type",
            repository_id="REP-000001",
            church_name_raw="First Congregational Church",
            baptized_name_raw="Arthur W. Colby",
            date_of_baptism="1873-05-11",
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    # Empty church_name_raw / bad date_of_baptism
    with pytest.raises(ModelFormatError, match="church_name_raw"):
        BaptismRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty church",
            repository_id="REP-000001",
            church_name_raw="   ",
            baptized_name_raw="Arthur W. Colby",
            date_of_baptism="1873-05-11",
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_of_baptism' payload"):
        BaptismRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad date",
            repository_id="REP-000001",
            church_name_raw="First Congregational Church",
            baptized_name_raw="Arthur W. Colby",
            date_of_baptism=18730511,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        BaptismRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        BaptismRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = "bad"
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        BaptismRecord.from_dict(bad_audit)
