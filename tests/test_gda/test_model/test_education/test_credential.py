"""Path: tests/test_gda/test_model/test_education/test_credential.py

Comprehensive unit tests for gda.model.education.credential.AcademicCredentialRecord.

Operational Role:
    Exercises AcademicCredentialRecord creation, URN:DIPLOMA and URN:SRC resolution,
    EducationLevel enum parsing, category and record_type bounds, dict/JSON
    round-trip serialization, and defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.sources import EducationLevel, SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.education import AcademicCredentialRecord

__version__ = "1.0.0+build.1"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN_DIP = "URN:DIPLOMA:1878:US_NH_DARTMOUTH:AB_DIPLOMA_1878"
_URN_SRC = "URN:SRC:1874:US_NH_CONCORD:HS_COMMENCEMENT_1874"


@pytest.mark.unit
@pytest.mark.smoke
def test_academic_credential_record_roundtrip() -> None:
    """Verify AcademicCredentialRecord full metadata and serialization."""
    now = IsoTimestamp("2026-11-01T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    issued_dt = EventDate.create("1878-06-27")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000020"),
        name_raw="Arthur W. Abbott",
        role=AssociatedRole.PRIMARY,
    )

    rec = AcademicCredentialRecord.create(
        source_id=_SID,
        source_urn=_URN_DIP,
        description="Bachelor of Arts Diploma issued by Dartmouth College to Arthur W. Abbott.",
        repository_id="REP-000001",
        institution_name_raw="  Dartmouth College  ",
        subject_name_raw="  Arthur W. Abbott  ",
        date_issued_or_published=issued_dt,
        record_category="education",
        record_type="diploma",
        education_level="  coll  ",
        institution_location_id="LOC-000040",
        subject_id="IND-000020",
        degree_or_credential="Artium Baccalaureus (A.B.)",
        graduation_year=1878,
        publication_title="General Catalogue of Dartmouth College",
        page_or_plate="p. 214",
        credential_note="Signed by President Samuel Colcord Bartlett.",
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.institution_name_raw == "Dartmouth College"
    assert rec.subject_name_raw == "Arthur W. Abbott"
    assert rec.education_level is EducationLevel.COLL
    assert rec.institution_location_id == LocationID("LOC-000040")
    assert rec.subject_id == IndividualID("IND-000020")
    assert rec.graduation_year == 1878
    assert str(rec) == "AcademicCredentialRecord [DIPLOMA] Arthur W. Abbott - Dartmouth College"

    payload = rec.to_dict()
    assert payload["education_level"] == "COLL"
    assert payload["graduation_year"] == 1878

    restored = AcademicCredentialRecord.from_dict(payload)
    assert restored == rec

    restored_json = AcademicCredentialRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct ArchivalURN, EducationLevel, AuditStamp, and EventDate instances
    direct_urn_rec = AcademicCredentialRecord.create(
        source_id=_SID,
        source_urn=ArchivalURN(_URN_DIP),
        description="Direct ArchivalURN and EducationLevel instance check.",
        repository_id="REP-000001",
        institution_name_raw="Dartmouth College",
        subject_name_raw="Arthur W. Abbott",
        date_issued_or_published=issued_dt,
        education_level=EducationLevel.GRAD,
    )
    assert direct_urn_rec.source_urn == ArchivalURN(_URN_DIP)
    assert direct_urn_rec.education_level is EducationLevel.GRAD

    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["date_issued_or_published"] = issued_dt
    assert AcademicCredentialRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_academic_credential_validation_and_minimal_roundtrip() -> None:
    """Verify AcademicCredentialRecord minimal round-trip and validation error branches."""
    minimal = AcademicCredentialRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_SRC,
        description="Concord High School Commencement Program, Class of 1874.",
        repository_id=RepositoryID("REP-000001"),
        institution_name_raw="Concord High School",
        subject_name_raw="Arthur W. Abbott",
        date_issued_or_published="1874-06-19",
        record_category=SourceRecordCategory.EDUCATION,
        record_type=SourceRecordType.COMMENCEMENT_PROGRAM,
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "education_level",
        "institution_location_id",
        "subject_id",
        "degree_or_credential",
        "graduation_year",
        "publication_title",
        "page_or_plate",
        "credential_note",
    ):
        assert opt_key not in min_dict
    assert AcademicCredentialRecord.from_dict(min_dict) == minimal

    # Direct constructor trims whitespace
    direct = AcademicCredentialRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        institution_name_raw="  Trimmed School  ",
        subject_name_raw="  Trimmed Student  ",
        date_issued_or_published=minimal.date_issued_or_published,
    )
    assert direct.institution_name_raw == "Trimmed School"
    assert direct.subject_name_raw == "Trimmed Student"

    # Validation branches
    with pytest.raises(ModelFormatError, match="Invalid Diploma URN syntax"):
        AcademicCredentialRecord.create(
            source_id=_SID,
            source_urn="URN:DIPLOMA:bad",
            description="Bad URN",
            repository_id="REP-000001",
            institution_name_raw="School",
            subject_name_raw="Student",
            date_issued_or_published="1874-06-19",
        )

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        AcademicCredentialRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong category",
            repository_id="REP-000001",
            institution_name_raw="School",
            subject_name_raw="Student",
            date_issued_or_published="1874-06-19",
            record_category=SourceRecordCategory.VITAL,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        AcademicCredentialRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong type",
            repository_id="REP-000001",
            institution_name_raw="School",
            subject_name_raw="Student",
            date_issued_or_published="1874-06-19",
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="institution_name_raw"):
        AcademicCredentialRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Empty institution",
            repository_id="REP-000001",
            institution_name_raw="   ",
            subject_name_raw="Student",
            date_issued_or_published="1874-06-19",
        )

    with pytest.raises(ModelFormatError, match="Invalid EducationLevel value"):
        AcademicCredentialRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad level",
            repository_id="REP-000001",
            institution_name_raw="School",
            subject_name_raw="Student",
            date_issued_or_published="1874-06-19",
            education_level="INVALID_LEVEL",
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_issued_or_published' payload"):
        AcademicCredentialRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad date",
            repository_id="REP-000001",
            institution_name_raw="School",
            subject_name_raw="Student",
            date_issued_or_published=1874,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        AcademicCredentialRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        AcademicCredentialRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        AcademicCredentialRecord.from_dict(bad_audit)
