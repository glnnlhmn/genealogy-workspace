"""Path: tests/test_gda/test_repository/test_manuscripts/test_repository.py

Unit and integration tests for Manuscripts domain SQLite repositories
(src/gda/repository/manuscripts/repository.py).
"""

from __future__ import annotations

from gda.core.enums.core import FactType
from gda.core.enums.sources import SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.source.manuscripts.bible import (
    BibleRegisterEntry,
    FamilyBibleRecord,
)
from gda.model.source.manuscripts.narrative import NarrativeManuscriptRecord
from gda.repository.manuscripts.repository import (
    FamilyBibleRepository,
    NarrativeManuscriptRepository,
)


def test_manuscripts_repositories_crud_and_queries(
    seeded_session: DatabaseSessionManager,
    golden_audit: AuditStamp,
    valid_repo_id: RepositoryID,
    sample_individual_id: IndividualID,
    sample_location_id: LocationID,
) -> None:
    """Verify FamilyBibleRepository and NarrativeManuscriptRepository CRUD and queries."""
    bible_repo = FamilyBibleRepository(session_manager=seeded_session)
    narr_repo = NarrativeManuscriptRepository(session_manager=seeded_session)

    bible = FamilyBibleRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000042"),
        source_urn=SourceURN("URN:SRC:1850:US_PA:BIB_042"),
        record_type=SourceRecordType.BIBLE_RECORD,
        description="Lehman Family Bible",
        repository_id=valid_repo_id,
        audit=golden_audit,
        family_surname="Lehman",
        original_owner_id=sample_individual_id,
        entries=(
            BibleRegisterEntry(
                line_number=1,
                event_type=FactType.BIRTH,
                subject_name_raw="John Lehman",
                subject_id=sample_individual_id,
            ),
        ),
    )
    bible_repo.upsert(bible)
    assert bible_repo.get_or_raise(bible.source_id) == bible
    assert len(bible_repo.find_by_family_surname("Lehman")) == 1
    assert len(bible_repo.find_by_original_owner("IND-000001")) == 1

    narr = NarrativeManuscriptRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000043"),
        source_urn=SourceURN("URN:SRC:1863:US_PA:NAR_043"),
        record_type=SourceRecordType.PERSONAL_LETTER,
        description="Civil War Letter",
        repository_id=valid_repo_id,
        audit=golden_audit,
        title_or_subject="Camp near Falmouth Letter",
        author_or_sender_id=sample_individual_id,
        recipient_id=IndividualID("IND-000002"),
        origin_place_id=sample_location_id,
        date_written_or_published=EventDate.from_dict("1863-01-18"),
    )
    narr_repo.upsert(narr)
    assert narr_repo.get_or_raise(narr.source_id) == narr
    assert len(narr_repo.find_by_author("IND-000001")) == 1
    assert len(narr_repo.find_by_recipient("IND-000002")) == 1
    assert len(narr_repo.find_by_origin_place("LOC-000001")) == 1
    assert len(narr_repo.find_by_written_year_range(1860, 1865)) == 1
