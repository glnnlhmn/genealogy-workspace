"""Path: tests/test_gda/test_repository/test_land/test_repository.py

Unit and integration tests for Land domain SQLite repositories
(src/gda/repository/land/repository.py).
"""

from __future__ import annotations

from gda.core.enums.land import DeedPartyRole, LandGrantBasis
from gda.core.enums.sources import SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    RepositoryID,
    SourceID,
)
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.source.land.deed import DeedParty, LandDeedRecord, LandParcel
from gda.model.source.land.grant import LandGrantRecord
from gda.repository.land.repository import (
    LandDeedRepository,
    LandGrantRepository,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_land_deed_and_grant_repositories(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify LandDeedRepository and LandGrantRepository CRUD and specialized queries."""
    deed_repo = LandDeedRepository(session_manager=seeded_session)
    grant_repo = LandGrantRepository(session_manager=seeded_session)

    deed = LandDeedRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000023"),
        source_urn=SourceURN("URN:SRC:1860:US_PA:DEED_023"),
        record_type=SourceRecordType.DEED_INDENTURE,
        description="Deed from John Lehman to Mary Miller",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        office_title="Recorder of Deeds, Cumberland County",
        recording_locator="Deed Book 2Z, Page 410",
        date_written=EventDate.from_dict("1860-04-01"),
        date_recorded=EventDate.from_dict("1860-04-15"),
        office_location_id=LocationID("LOC-000001"),
        deed_book="2Z",
        page_number="410",
        dower_relinquished=False,
        grantors=(
            DeedParty(
                full_name="John Lehman",
                party_role=DeedPartyRole.GRANTOR,
                individual_id=IndividualID("IND-000001"),
            ),
        ),
        grantees=(
            DeedParty(
                full_name="Mary Miller",
                party_role=DeedPartyRole.GRANTEE,
                individual_id=IndividualID("IND-000002"),
            ),
        ),
        parcel=LandParcel(
            location_raw="South Middleton Township, Cumberland County",
            location_id=LocationID("LOC-000001"),
            acreage_numeric=85.5,
        ),
    )

    deed_repo.upsert(deed)
    assert deed_repo.get_or_raise(deed.source_id) == deed
    assert len(deed_repo.find_by_grantor("IND-000001")) == 1
    assert len(deed_repo.find_by_grantee("IND-000002")) == 1
    assert len(deed_repo.find_by_parcel_location("LOC-000001")) == 1
    assert len(deed_repo.find_by_written_year_range(1855, 1865)) == 1

    grant = LandGrantRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000024"),
        source_urn=SourceURN("URN:SRC:1795:US_PA:PAT_024"),
        record_type=SourceRecordType.PATENT,
        description="Commonwealth of Pennsylvania Land Patent to John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        issuing_authority="Commonwealth of Pennsylvania",
        instrument_locator="Patent Book P-26, Page 88",
        patentee_name_raw="John Lehman",
        office_location_id=LocationID("LOC-000001"),
        patent_or_warrant_number="W-1794-102",
        grant_basis=LandGrantBasis.PROPRIETARY_GRANT,
        patentee_id=IndividualID("IND-000001"),
        assignee_id=IndividualID("IND-000002"),
        date_warrant_or_entry=EventDate.from_dict("1794-03-10"),
        date_surveyed=EventDate.from_dict("1794-09-22"),
        date_patented=EventDate.from_dict("1795-05-01"),
        parcel=LandParcel(
            location_raw="Cumberland County, PA",
            location_id=LocationID("LOC-000001"),
            tract_name="Lehman's Delight",
            acreage_numeric=212.0,
        ),
    )

    grant_repo.upsert(grant)
    assert grant_repo.get_or_raise(grant.source_id) == grant
    assert len(grant_repo.find_by_patentee("IND-000001")) == 1
    assert len(grant_repo.find_by_assignee("IND-000002")) == 1
    assert len(grant_repo.find_by_parcel_location("LOC-000001")) == 1
    assert len(grant_repo.find_by_patented_year_range(1790, 1800)) == 1
