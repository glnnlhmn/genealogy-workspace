"""Path: tests/test_gda/test_repository/test_manuscripts/test_collection.py

Unit and integration tests for Manuscripts domain collections
(src/gda/repository/manuscripts/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from gda.core.enums.sources import SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.source.manuscripts.bible import FamilyBibleRecord
from gda.model.source.manuscripts.narrative import NarrativeManuscriptRecord
from gda.repository.manuscripts.collection import (
    FamilyBibleCollection,
    NarrativeManuscriptCollection,
)


def test_manuscripts_collections_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    golden_audit: AuditStamp,
    valid_repo_id: RepositoryID,
    sample_individual_id: IndividualID,
    sample_location_id: LocationID,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and JSON round-tripping for Manuscripts collections."""
    # 1. FamilyBibleCollection
    bible_coll = FamilyBibleCollection.from_database(seeded_session)
    bible = FamilyBibleRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000142"),
        source_urn=SourceURN("URN:SRC:1850:US_PA:BIB_142"),
        record_type=SourceRecordType.BIBLE_RECORD,
        description="Bible",
        repository_id=valid_repo_id,
        audit=golden_audit,
        family_surname="Lehman",
        original_owner_id=sample_individual_id,
    )
    bible_coll.add(bible)
    assert len(bible_coll.find_by_family_surname("Lehman")) == 1
    assert len(bible_coll.find_by_original_owner("IND-000001")) == 1
    bible_coll.edit(bible.source_id, original_owner_id=None)
    assert len(bible_coll.find_by_original_owner("IND-000001")) == 0
    bible_coll.edit(bible.source_id, description="Bible None Branch")
    bible_coll.add(
        dataclasses.replace(
            bible,
            source_id=SourceID("00000000-0000-4000-8000-000000000342"),
            source_urn=SourceURN("URN:SRC:1850:US_PA:BIB_342"),
            original_owner_id=None,
        )
    )
    p_bib = tmp_path / "bible.json"
    bible_coll.export_file(p_bib)
    FamilyBibleCollection().import_file(p_bib)

    # 2. NarrativeManuscriptCollection
    narr_coll = NarrativeManuscriptCollection.from_database(seeded_session)
    narr = NarrativeManuscriptRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000143"),
        source_urn=SourceURN("URN:SRC:1863:US_PA:NAR_143"),
        record_type=SourceRecordType.PERSONAL_LETTER,
        description="Letter",
        repository_id=valid_repo_id,
        audit=golden_audit,
        title_or_subject="Letter",
        author_or_sender_id=sample_individual_id,
        origin_place_id=sample_location_id,
    )
    narr_coll.add(narr)
    assert len(narr_coll.find_by_author("IND-000001")) == 1
    assert len(narr_coll.find_by_origin_place("LOC-000001")) == 1
    narr_coll.edit(
        narr.source_id,
        author_or_sender_id=None,
        origin_place_id=None,
    )
    assert len(narr_coll.find_by_author("IND-000001")) == 0
    assert len(narr_coll.find_by_origin_place("LOC-000001")) == 0
    narr_coll.edit(narr.source_id, description="Narr None Branch")
    narr_coll.add(
        dataclasses.replace(
            narr,
            source_id=SourceID("00000000-0000-4000-8000-000000000343"),
            source_urn=SourceURN("URN:SRC:1863:US_PA:NAR_343"),
            author_or_sender_id=None,
            origin_place_id=None,
        )
    )
    p_nar = tmp_path / "narr.json"
    narr_coll.export_file(p_nar)
    NarrativeManuscriptCollection().import_file(p_nar)
