"""Path: tests/test_gda/test_repository/test_orgs/test_collection.py

Unit and integration tests for Orgs domain collections
(src/gda/repository/orgs/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from gda.core.enums.orgs import OrganizationCategory
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
from gda.repository.orgs.collection import (
    OrganizationMembershipCollection,
    OrganizationRosterCollection,
)


def test_orgs_collections_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    golden_audit: AuditStamp,
    valid_repo_id: RepositoryID,
    sample_individual_id: IndividualID,
    sample_location_id: LocationID,
    sample_organization_id: OrganizationID,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and JSON round-tripping for Orgs collections."""
    # 1. OrganizationMembershipCollection
    mem_coll = OrganizationMembershipCollection.from_database(seeded_session)
    membership = OrganizationMembershipRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000144"),
        source_urn=SourceURN("URN:SRC:1880:US_PA:MEM_144"),
        record_type=SourceRecordType.LODGE_RECORD,
        description="Membership",
        repository_id=valid_repo_id,
        audit=golden_audit,
        individual_id=sample_individual_id,
        organization_name_raw="Zion",
        org_id=sample_organization_id,
    )
    mem_coll.add(membership)
    assert len(mem_coll.find_by_individual("IND-000001")) == 1
    assert len(mem_coll.find_by_organization("ORG-000001")) == 1
    mem_coll.edit(membership.source_id, org_id=None)
    assert len(mem_coll.find_by_organization("ORG-000001")) == 0
    mem_coll.edit(membership.source_id, description="Mem None Branch")
    mem_coll.add(
        dataclasses.replace(
            membership,
            source_id=SourceID("00000000-0000-4000-8000-000000000344"),
            source_urn=SourceURN("URN:SRC:1880:US_PA:MEM_344"),
            org_id=None,
        )
    )
    p_mem = tmp_path / "mem.json"
    mem_coll.export_file(p_mem)
    OrganizationMembershipCollection().import_file(p_mem)

    # 2. OrganizationRosterCollection
    ros_coll = OrganizationRosterCollection.from_database(seeded_session)
    roster = OrganizationRosterRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000145"),
        source_urn=SourceURN("URN:SRC:1885:US_PA:ROS_145"),
        record_type=SourceRecordType.MEMBERSHIP_ROSTER,
        description="Roster",
        repository_id=valid_repo_id,
        audit=golden_audit,
        enumeration_year=HistoricalYear(1885),
        jurisdiction_raw="Carlisle",
        jurisdiction_id=sample_location_id,
        organization_name_raw="Zion",
        org_id=sample_organization_id,
        org_category=OrganizationCategory.RELIGIOUS,
        entries=(
            OrganizationRosterEntry(
                entry_urn=SourceURN("URN:SRC:1885:US_PA:ROS_145_L1"),
                line_number=1,
                member_name_verbatim="John Lehman",
            ),
        ),
    )
    ros_coll.add(roster)
    assert len(ros_coll.find_by_organization("ORG-000001")) == 1
    assert len(ros_coll.find_by_jurisdiction("LOC-000001")) == 1
    ros_coll.edit(roster.source_id, org_id=None, jurisdiction_id=None)
    assert len(ros_coll.find_by_organization("ORG-000001")) == 0
    assert len(ros_coll.find_by_jurisdiction("LOC-000001")) == 0
    ros_coll.edit(roster.source_id, description="Roster None Branch")
    ros_coll.add(
        dataclasses.replace(
            roster,
            source_id=SourceID("00000000-0000-4000-8000-000000000345"),
            source_urn=SourceURN("URN:SRC:1885:US_PA:ROS_345"),
            org_id=None,
            jurisdiction_id=None,
        )
    )
    p_ros = tmp_path / "ros.json"
    ros_coll.export_file(p_ros)
    OrganizationRosterCollection().import_file(p_ros)
