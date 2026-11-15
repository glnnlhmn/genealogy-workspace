"""Path: tests/test_gda/test_model/test_source/test_vital/test_vital_divorce.py

Comprehensive unit tests for gda.model.source.vital.divorce.DivorceRecord.

Operational Role:
    Exercises factory creation, SourceRecord inheritance, LEGAL/VITAL category
    bounds, decree type parsing, dict/JSON round-trip serialization, and
    defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import DivorceDecreeType, LegalPlaintiff
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.vital import DivorceRecord

__version__ = "1.0.0+build.2"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN = "URN:SRC:1921:US_NH_MERRIMACK:DIVORCE_114"
_URN_MIN = "URN:SRC:1922:US_NH_MERRIMACK:DIVORCE_115"


@pytest.mark.unit
@pytest.mark.smoke
def test_divorce_record_create_and_roundtrip() -> None:
    """Verify DivorceRecord.create with full decree details and serialization."""
    now = IsoTimestamp("2026-05-04T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    dom = EventDate.create("1912-09-18")
    sep = EventDate.create("1919-05-01")
    granted = EventDate.create("1921-10-12")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000005"),
        name_raw="Hon. William H. Sawyer",
        role=AssociatedRole.OFFICIAL,
    )

    rec = DivorceRecord.create(
        source_id=_SID,
        source_urn=_URN,
        description="Divorce Decree of Charles E. Marston and Clara B. Marston.",
        repository_id="REP-000001",
        court_name="  Superior Court, Merrimack County  ",
        husband_name_raw="  Charles E. Marston  ",
        wife_name_raw="  Clara B. Marston  ",
        date_decree_granted=granted,
        record_category="legal",
        record_type="divorce_decree",
        docket_number="EQ-1921-114",
        state_file_number="NH-DIV-1921-0114",
        jurisdiction_raw="Merrimack County, NH",
        jurisdiction_id="LOC-000002",
        husband_id="IND-000010",
        wife_id="IND-000011",
        wife_maiden_name_raw="Flanders",
        date_of_marriage=dom,
        place_of_marriage_raw="Concord, NH",
        date_of_separation=sep,
        plaintiff="wife",
        decree_type="ABSOLUTE",
        legal_grounds="Abandonment and refusal to cohabit",
        minor_children_count=2,
        alimony_awarded=True,
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.court_name == "Superior Court, Merrimack County"
    assert rec.husband_name_raw == "Charles E. Marston"
    assert rec.wife_name_raw == "Clara B. Marston"
    assert rec.jurisdiction_id == LocationID("LOC-000002")
    assert rec.husband_id == IndividualID("IND-000010")
    assert rec.wife_id == IndividualID("IND-000011")
    assert rec.plaintiff is LegalPlaintiff.WIFE
    assert rec.decree_type is DivorceDecreeType.ABSOLUTE
    assert rec.minor_children_count == 2
    assert rec.alimony_awarded is True
    assert str(rec) == "DivorceRecord [Charles E. Marston v. Clara B. Marston] (1921-10-12)"

    payload = rec.to_dict()
    assert payload["docket_number"] == "EQ-1921-114"
    assert payload["decree_type"] == "Absolute (A Vinculo Matrimonii)"

    restored = DivorceRecord.from_dict(payload)
    assert restored == rec

    restored_json = DivorceRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct AuditStamp and EventDate objects passed in from_dict
    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["date_decree_granted"] = granted
    direct_payload["date_of_marriage"] = dom
    direct_payload["date_of_separation"] = sep
    assert DivorceRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_divorce_record_validation_and_minimal_roundtrip() -> None:
    """Verify DivorceRecord minimal round-trip and validation error branches."""
    minimal = DivorceRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_MIN,
        description="Vital Divorce Report.",
        repository_id=RepositoryID("REP-000001"),
        court_name="Merrimack County Superior Court",
        husband_name_raw="George A. Colby",
        wife_name_raw="Alice M. Colby",
        date_decree_granted="1922-04-05",
        record_category=SourceRecordCategory.VITAL,
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "docket_number",
        "state_file_number",
        "jurisdiction_raw",
        "jurisdiction_id",
        "husband_id",
        "wife_id",
        "wife_maiden_name_raw",
        "date_of_marriage",
        "place_of_marriage_raw",
        "date_of_separation",
        "plaintiff",
        "legal_grounds",
        "minor_children_count",
        "alimony_awarded",
    ):
        assert opt_key not in min_dict
    assert DivorceRecord.from_dict(min_dict) == minimal

    # Direct constructor trims court_name, husband_name_raw, and wife_name_raw
    direct = DivorceRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        court_name="  Trimmed Court  ",
        husband_name_raw="  Trimmed Husband  ",
        wife_name_raw="  Trimmed Wife  ",
        date_decree_granted=EventDate.create("1922-04-05"),
    )
    assert direct.court_name == "Trimmed Court"
    assert direct.husband_name_raw == "Trimmed Husband"
    assert direct.wife_name_raw == "Trimmed Wife"

    # Disallowed category / record_type / decree_type
    with pytest.raises(ModelFormatError, match="requires record_category in"):
        DivorceRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong category",
            repository_id="REP-000001",
            court_name="Court",
            husband_name_raw="Husband",
            wife_name_raw="Wife",
            date_decree_granted="1922-04-05",
            record_category=SourceRecordCategory.CHURCH,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        DivorceRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong type",
            repository_id="REP-000001",
            court_name="Court",
            husband_name_raw="Husband",
            wife_name_raw="Wife",
            date_decree_granted="1922-04-05",
            record_type=SourceRecordType.MARRIAGE_LICENSE,
        )

    with pytest.raises(ModelFormatError, match="Invalid DivorceDecreeType value"):
        DivorceRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad decree type",
            repository_id="REP-000001",
            court_name="Court",
            husband_name_raw="Husband",
            wife_name_raw="Wife",
            date_decree_granted="1922-04-05",
            decree_type="NOT_A_DECREE",
        )

    # Empty court / husband / wife / bad date
    with pytest.raises(ModelFormatError, match="court_name"):
        DivorceRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty court",
            repository_id="REP-000001",
            court_name="   ",
            husband_name_raw="Husband",
            wife_name_raw="Wife",
            date_decree_granted="1922-04-05",
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_decree_granted' payload"):
        DivorceRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad date",
            repository_id="REP-000001",
            court_name="Court",
            husband_name_raw="Husband",
            wife_name_raw="Wife",
            date_decree_granted=19220405,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        DivorceRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        DivorceRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = "bad"
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        DivorceRecord.from_dict(bad_audit)
