"""Path: tests/test_gda/test_model/test_source/test_orgs/test_orgs_membership.py

Comprehensive unit tests for gda.model.source.orgs.membership.OrganizationMembershipRecord.

Operational Role:
    Exercises factory creation, SourceRecord inheritance, category enforcement,
    period date accessors, dict/JSON round-trip serialization, and defensive
    deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.orgs import AffiliationType, MembershipStatus, OrganizationCategory
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, MediaID, OrganizationID, RepositoryID, SourceID
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.tombstone import Tombstone
from gda.model.source.orgs import OrganizationMembershipRecord

__version__ = "1.0.0+build.4"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_SRC_URN = "URN:SRC:1892:US_NH_CONCORD:CHURCH-ROLL-P12"
_SRC_URN_MIN = "URN:SRC:1901:US_NH_CONCORD:LODGE70-ENTRY1"


@pytest.mark.unit
@pytest.mark.smoke
def test_membership_record_create_and_roundtrip() -> None:
    """Verify OrganizationMembershipRecord.create, properties, and dict/JSON serialization."""
    now = IsoTimestamp("2026-03-01T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    period = TimePeriod(
        start_date=EventDate.create("1892"),
        end_date=EventDate.create("1914"),
    )
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000002"),
        name_raw="Rev. Thomas Abbott",
        role=AssociatedRole.CLERGY,
    )

    rec = OrganizationMembershipRecord.create(
        source_id=_SID,
        source_urn=_SRC_URN,
        description="Admission of John Doe to First Congregational Church Men's Choir.",
        repository_id="REP-000001",
        individual_id="IND-000001",
        organization_name_raw="  First Congregational Church Men's Choir  ",
        record_category="church",
        record_type="membership_roster",
        org_id="ORG-000050",
        org_category="cultural_arts",
        affiliation_type="officer",
        membership_status="active",
        role_or_title_raw="First Tenor / Choir Secretary",
        degree_or_rank_raw="Senior Member",
        membership_period=period,
        dues_or_contribution_raw="$2.00 annual pew & choir assessment",
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.source_id == SourceID(_SID)
    assert rec.record_category is SourceRecordCategory.CHURCH
    assert rec.record_type is SourceRecordType.MEMBERSHIP_ROSTER
    assert rec.individual_id == IndividualID("IND-000001")
    assert rec.organization_name_raw == "First Congregational Church Men's Choir"
    assert rec.org_id == OrganizationID("ORG-000050")
    assert rec.org_category is OrganizationCategory.CULTURAL_ARTS
    assert rec.affiliation_type is AffiliationType.OFFICER
    assert rec.membership_status is MembershipStatus.ACTIVE
    assert rec.date_joined == EventDate.create("1892")
    assert rec.date_ended == EventDate.create("1914")
    assert rec.media_count == 1
    assert rec.participant_count == 1
    assert rec.is_deprecated is True
    assert "First Congregational Church Men's Choir" in str(rec)

    payload = rec.to_dict()
    assert payload["org_id"] == "ORG-000050"
    assert payload["role_or_title_raw"] == "First Tenor / Choir Secretary"
    assert payload["degree_or_rank_raw"] == "Senior Member"
    assert payload["dues_or_contribution_raw"] == "$2.00 annual pew & choir assessment"
    assert payload["tombstone"]["superseded_by"] == _SID_2

    restored = OrganizationMembershipRecord.from_dict(payload)
    assert restored == rec

    restored_json = OrganizationMembershipRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct AuditStamp and TimePeriod objects in from_dict
    direct_obj_payload = dict(payload)
    direct_obj_payload["audit"] = audit
    direct_obj_payload["membership_period"] = period
    assert OrganizationMembershipRecord.from_dict(direct_obj_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_membership_record_validation_and_minimal_roundtrip() -> None:
    """Verify category constraints, whitespace hygiene, and minimal serialization."""
    minimal = OrganizationMembershipRecord.create(
        source_id=SourceID(_SID),
        source_urn=_SRC_URN_MIN,
        description="Initiation into Eureka Lodge No. 70.",
        repository_id=RepositoryID("REP-000001"),
        individual_id=IndividualID("IND-000010"),
        organization_name_raw="Eureka Lodge No. 70, F. & A.M.",
        media_ids=[MediaID(_MID)],
    )
    assert minimal.date_joined is None
    assert minimal.date_ended is None
    minimal_dict = minimal.to_dict()
    assert "org_id" not in minimal_dict
    assert "role_or_title_raw" not in minimal_dict
    assert "degree_or_rank_raw" not in minimal_dict
    assert "membership_period" not in minimal_dict
    assert "dues_or_contribution_raw" not in minimal_dict
    assert OrganizationMembershipRecord.from_dict(minimal_dict) == minimal

    # Direct constructor trims organization_name_raw
    direct = OrganizationMembershipRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct init test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        individual_id=IndividualID("IND-000010"),
        organization_name_raw="  Trimmed Lodge Name  ",
    )
    assert direct.organization_name_raw == "Trimmed Lodge Name"

    # Disallowed SourceRecordCategory
    with pytest.raises(ModelFormatError, match="requires record_category in"):
        OrganizationMembershipRecord.create(
            source_id=_SID,
            source_urn="URN:SRC:1900:US_NH_CONCORD:CENSUS-ENTRY1",
            description="Invalid category test",
            repository_id="REP-000001",
            individual_id="IND-000010",
            organization_name_raw="Eureka Lodge",
            record_category=SourceRecordCategory.CENSUS,
        )

    # Empty organization_name_raw
    with pytest.raises(ModelFormatError, match="organization_name_raw"):
        OrganizationMembershipRecord.create(
            source_id=_SID,
            source_urn="URN:SRC:1901:US_NH_CONCORD:LODGE70-ENTRY2",
            description="Empty org name test",
            repository_id="REP-000001",
            individual_id="IND-000010",
            organization_name_raw="   ",
        )

    # from_dict validation errors
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        OrganizationMembershipRecord.from_dict([])  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        OrganizationMembershipRecord.from_dict({"source_id": _SID})

    bad_audit = dict(minimal_dict)
    bad_audit["audit"] = "invalid-audit"
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        OrganizationMembershipRecord.from_dict(bad_audit)
