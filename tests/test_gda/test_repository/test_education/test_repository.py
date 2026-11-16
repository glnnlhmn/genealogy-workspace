"""Path: tests/test_gda/test_repository/test_education/test_repository.py

Unit and integration tests for AcademicCredentialRepository
(src/gda/repository/education/repository.py).
"""

from __future__ import annotations

from gda.core.enums.sources import EducationLevel, SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.source.education.credential import AcademicCredentialRecord
from gda.repository.education.repository import AcademicCredentialRepository


def test_academic_credential_repository_crud_and_queries(
    seeded_session: DatabaseSessionManager,
    golden_audit: AuditStamp,
    valid_repo_id: RepositoryID,
    sample_individual_id: IndividualID,
    sample_location_id: LocationID,
) -> None:
    """Verify AcademicCredentialRepository CRUD and specialized query methods."""
    repo = AcademicCredentialRepository(session_manager=seeded_session)
    cred = AcademicCredentialRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000041"),
        source_urn=SourceURN("URN:SRC:1874:US_PA:EDU_041"),
        record_type=SourceRecordType.DIPLOMA,
        description="Bachelor of Arts Diploma",
        repository_id=valid_repo_id,
        audit=golden_audit,
        institution_name_raw="Dickinson College",
        subject_name_raw="John Lehman",
        date_issued_or_published=EventDate.from_dict("1874-06-25"),
        education_level=EducationLevel.COLL,
        institution_location_id=sample_location_id,
        subject_id=sample_individual_id,
        degree_or_credential="Bachelor of Arts",
        graduation_year=1874,
    )

    repo.upsert(cred)
    assert repo.get_or_raise(cred.source_id) == cred
    assert len(repo.find_by_subject("IND-000001")) == 1
    assert len(repo.find_by_institution_location("LOC-000001")) == 1
    assert len(repo.find_by_graduation_year(1874)) == 1
    assert len(repo.find_by_issued_year_range(1870, 1875)) == 1
    assert len(repo.find_by_issued_year_range(1880, 1885)) == 0
