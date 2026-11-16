"""Path: tests/test_gda/test_repository/test_other/test_repository.py

Unit and integration tests for OtherMiscellaneousRepository
(src/gda/repository/other/repository.py).
"""

from __future__ import annotations

from gda.core.enums.sources import SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.source.other.miscellaneous import OtherMiscellaneousRecord
from gda.repository.other.repository import OtherMiscellaneousRepository


def test_other_miscellaneous_repository_crud_and_queries(
    seeded_session: DatabaseSessionManager,
    golden_audit: AuditStamp,
    valid_repo_id: RepositoryID,
    sample_location_id: LocationID,
) -> None:
    """Verify OtherMiscellaneousRepository CRUD and specialized query methods."""
    repo = OtherMiscellaneousRepository(session_manager=seeded_session)
    misc = OtherMiscellaneousRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000046"),
        source_urn=SourceURN("URN:SRC:1892:US_PA:MSC_046"),
        record_type=SourceRecordType.RECEIPT,
        description="Blacksmith Receipt",
        repository_id=valid_repo_id,
        audit=golden_audit,
        item_date=EventDate.from_dict("1892-07-14"),
        organization_or_entity_name="Lehman Blacksmithing",
        organization_location_id=sample_location_id,
    )

    repo.upsert(misc)
    assert repo.get_or_raise(misc.source_id) == misc
    assert len(repo.find_by_organization_location("LOC-000001")) == 1
    assert len(repo.find_by_item_year_range(1890, 1895)) == 1
    assert len(repo.find_by_item_year_range(1900, 1905)) == 0
