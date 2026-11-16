"""Path: tests/test_gda/test_repository/test_other/test_collection.py

Unit and integration tests for OtherMiscellaneousCollection
(src/gda/repository/other/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from gda.core.enums.sources import SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.source.other.miscellaneous import OtherMiscellaneousRecord
from gda.repository.other.collection import OtherMiscellaneousCollection


def test_other_miscellaneous_collection_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    golden_audit: AuditStamp,
    valid_repo_id: RepositoryID,
    sample_location_id: LocationID,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and JSON round-tripping for OtherMiscellaneousCollection."""
    coll = OtherMiscellaneousCollection.from_database(seeded_session)
    misc = OtherMiscellaneousRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000146"),
        source_urn=SourceURN("URN:SRC:1892:US_PA:MSC_146"),
        record_type=SourceRecordType.RECEIPT,
        description="Receipt",
        repository_id=valid_repo_id,
        audit=golden_audit,
        item_date=EventDate.from_dict("1892-07-14"),
        organization_location_id=sample_location_id,
    )
    coll.add(misc)
    assert len(coll.find_by_organization_location("LOC-000001")) == 1

    coll.edit(misc.source_id, organization_location_id=None)
    assert len(coll.find_by_organization_location("LOC-000001")) == 0
    coll.edit(misc.source_id, description="Misc None Branch")
    coll.add(
        dataclasses.replace(
            misc,
            source_id=SourceID("00000000-0000-4000-8000-000000000346"),
            source_urn=SourceURN("URN:SRC:1892:US_PA:MSC_346"),
            organization_location_id=None,
        )
    )
    p_msc = tmp_path / "misc.json"
    coll.export_file(p_msc)
    OtherMiscellaneousCollection().import_file(p_msc)
