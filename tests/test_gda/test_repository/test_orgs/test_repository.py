"""Path: tests/test_gda/test_repository/test_orgs/test_repository.py

Unit and integration tests for Orgs domain SQLite repositories
(src/gda/repository/orgs/repository.py).
"""

from __future__ import annotations

from gda.core.enums.orgs import (
    AffiliationType,
    MembershipStatus,
    OrganizationCategory,
)
from gda.core.enums.sources import SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    OrganizationID,
    RepositoryID,
    SourceID,
)
from gda.model.atom.urn import SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.source.orgs.membership import OrganizationMembershipRecord
from gda.model.source.orgs.roster import (
    OrganizationRosterEntry,
    OrganizationRosterRecord,
)
from gda.repository.orgs.repository import (
    OrganizationMembershipRepository,
    OrganizationRosterRepository,
)


def test_orgs_membership_and_roster_repositories(
    seeded_session: DatabaseSessionManager,
    golden_audit: AuditStamp,
    valid_repo_id: RepositoryID,
    sample_individual_id: IndividualID,
    sample_location_id: LocationID,
    sample_organization_id: OrganizationID,
) -> None:
    """Verify OrganizationMembershipRepository and OrganizationRosterRepository CRUD and queries."""
    mem_repo = OrganizationMembershipRepository(session_manager=seeded_session)
    ros_repo = OrganizationRosterRepository(session_manager=seeded_session)

    membership = OrganizationMembershipRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000044"),
        source_urn=SourceURN("URN:SRC:1880:US_PA:MEM_044"),
        record_type=SourceRecordType.LODGE_RECORD,
        description="Lodge Membership",
        repository_id=valid_repo_id,
        audit=golden_audit,
        individual_id=sample_individual_id,
        organization_name_raw="Zion Lutheran Church",
        org_id=sample_organization_id,
        org_category=OrganizationCategory.RELIGIOUS,
        affiliation_type=AffiliationType.MEMBER,
        membership_status=MembershipStatus.ACTIVE,
    )
    mem_repo.upsert(membership)
    assert mem_repo.get_or_raise(membership.source_id) == membership
    assert len(mem_repo.find_by_individual("IND-000001")) == 1
    assert len(mem_repo.find_by_organization("ORG-000001")) == 1

    roster = OrganizationRosterRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000045"),
        source_urn=SourceURN("URN:SRC:1885:US_PA:ROS_045"),
        record_type=SourceRecordType.MEMBERSHIP_ROSTER,
        description="Roll of Communicants",
        repository_id=valid_repo_id,
        audit=golden_audit,
        enumeration_year=HistoricalYear(1885),
        jurisdiction_raw="Carlisle, PA",
        jurisdiction_id=sample_location_id,
        organization_name_raw="Zion Lutheran Church",
        org_id=sample_organization_id,
        org_category=OrganizationCategory.RELIGIOUS,
        entries=(
            OrganizationRosterEntry(
                entry_urn=SourceURN("URN:SRC:1885:US_PA:ROS_045_L1"),
                line_number=1,
                member_name_verbatim="John Lehman",
                individual_id=sample_individual_id,
            ),
        ),
    )
    ros_repo.upsert(roster)
    assert ros_repo.get_or_raise(roster.source_id) == roster
    assert len(ros_repo.find_by_organization("ORG-000001")) == 1
    assert len(ros_repo.find_by_jurisdiction("LOC-000001")) == 1
    assert len(ros_repo.find_by_year(1885)) == 1
