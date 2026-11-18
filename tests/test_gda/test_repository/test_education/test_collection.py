"""Path: tests/test_gda/test_repository/test_education/test_collection.py

Unit and integration tests for AcademicCredentialCollection
(src/gda/repository/education/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from gda.core.enums.sources import SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.source.education.credential import AcademicCredentialRecord
from gda.repository.education.collection import AcademicCredentialCollection


def test_academic_credential_collection_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    golden_audit: AuditStamp,
    valid_repo_id: RepositoryID,
    sample_individual_id: IndividualID,
    sample_location_id: LocationID,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and JSON round-tripping for AcademicCredentialCollection."""
    coll = AcademicCredentialCollection.from_database(seeded_session)
    cred = AcademicCredentialRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000141"),
        source_urn=SourceURN("URN:SRC:1874:US_PA:EDU_141"),
        record_type=SourceRecordType.DIPLOMA,
        description="Diploma",
        repository_id=valid_repo_id,
        audit=golden_audit,
        institution_name_raw="Dickinson College",
        subject_name_raw="John Lehman",
        date_issued_or_published=EventDate.from_dict("1874-06-25"),
        institution_location_id=sample_location_id,
        subject_id=sample_individual_id,
    )
    coll.add(cred)
    assert len(coll.find_by_subject("IND-000001")) == 1
    assert len(coll.find_by_institution_location("LOC-000001")) == 1

    coll.edit(
        cred.source_id,
        subject_id=None,
        institution_location_id=None,
    )
    assert len(coll.find_by_subject("IND-000001")) == 0
    assert len(coll.find_by_institution_location("LOC-000001")) == 0
    coll.edit(cred.source_id, description="Edu None Branch")
    coll.add(
        dataclasses.replace(
            cred,
            source_id=SourceID("00000000-0000-4000-8000-000000000341"),
            source_urn=SourceURN("URN:SRC:1874:US_PA:EDU_341"),
            subject_id=None,
            institution_location_id=None,
        )
    )
    p_edu = tmp_path / "edu.json"
    coll.export_file(p_edu)
    AcademicCredentialCollection().import_file(p_edu)
