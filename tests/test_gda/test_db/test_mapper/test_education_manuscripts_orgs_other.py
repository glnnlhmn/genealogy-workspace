"""Path: tests/test_gda/test_db/test_mapper/test_education_manuscripts_orgs_other.py

Unit tests for Education, Manuscripts, Orgs, and Other row mappers
(src/gda/db/mapper/education_manuscripts_orgs_other.py).
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import FactType
from gda.core.enums.orgs import (
    AffiliationType,
    MembershipStatus,
    OrganizationCategory,
)
from gda.core.enums.sources import EducationLevel, SourceRecordType
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.education_manuscripts_orgs_other import (
    AcademicCredentialRecordMapper,
    FamilyBibleRecordMapper,
    NarrativeManuscriptRecordMapper,
    OrganizationMembershipRecordMapper,
    OrganizationRosterRecordMapper,
    OtherMiscellaneousRecordMapper,
)
from gda.model.atom.date import IsoTimestamp
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
from gda.model.base.date import EventDate
from gda.model.source.education.credential import AcademicCredentialRecord
from gda.model.source.manuscripts.bible import (
    BibleRegisterEntry,
    FamilyBibleRecord,
)
from gda.model.source.manuscripts.narrative import NarrativeManuscriptRecord
from gda.model.source.orgs.membership import OrganizationMembershipRecord
from gda.model.source.orgs.roster import (
    OrganizationRosterEntry,
    OrganizationRosterRecord,
)
from gda.model.source.other.miscellaneous import OtherMiscellaneousRecord


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_education_manuscripts_orgs_other_mappers_roundtrip() -> None:
    """Verify to_row and from_row round-trip across all 6 Batch 4 mappers."""
    edu_mapper = AcademicCredentialRecordMapper()
    cred = AcademicCredentialRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000041"),
        source_urn=SourceURN("URN:SRC:1874:US_PA:EDU_041"),
        record_type=SourceRecordType.DIPLOMA,
        description="Bachelor of Arts Diploma, Dickinson College",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        institution_name_raw="Dickinson College",
        subject_name_raw="John Lehman",
        date_issued_or_published=EventDate.from_dict("1874-06-25"),
        education_level=EducationLevel.COLL,
        institution_location_id=LocationID("LOC-000001"),
        subject_id=IndividualID("IND-000001"),
        degree_or_credential="Bachelor of Arts",
        graduation_year=1874,
    )
    assert edu_mapper.from_row(edu_mapper.to_row(cred)) == cred

    bible_mapper = FamilyBibleRecordMapper()
    bible = FamilyBibleRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000042"),
        source_urn=SourceURN("URN:SRC:1850:US_PA:BIB_042"),
        record_type=SourceRecordType.BIBLE_RECORD,
        description="Lehman Family Bible Register",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        family_surname="Lehman",
        edition_imprint="Kimber & Sharpless, Philadelphia",
        publication_year=1848,
        original_owner_raw="Daniel Lehman",
        original_owner_id=IndividualID("IND-000001"),
        entries=(
            BibleRegisterEntry(
                line_number=1,
                event_type=FactType.BIRTH,
                subject_name_raw="John Lehman",
                subject_id=IndividualID("IND-000001"),
                event_date=EventDate.from_dict("1852-01-03"),
                place_id=LocationID("LOC-000001"),
            ),
        ),
    )
    assert bible_mapper.from_row(bible_mapper.to_row(bible)) == bible

    narr_mapper = NarrativeManuscriptRecordMapper()
    narr = NarrativeManuscriptRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000043"),
        source_urn=SourceURN("URN:SRC:1863:US_PA:NAR_043"),
        record_type=SourceRecordType.PERSONAL_LETTER,
        description="Letter from John Lehman to Mary Miller",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        title_or_subject="Camp near Falmouth, Virginia Letter",
        author_or_sender_raw="John Lehman",
        author_or_sender_id=IndividualID("IND-000001"),
        recipient_raw="Mary Miller",
        recipient_id=IndividualID("IND-000002"),
        origin_place_id=LocationID("LOC-000001"),
        destination_place_id=LocationID("LOC-000002"),
        date_written_or_published=EventDate.from_dict("1863-01-18"),
    )
    assert narr_mapper.from_row(narr_mapper.to_row(narr)) == narr

    mem_mapper = OrganizationMembershipRecordMapper()
    membership = OrganizationMembershipRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000044"),
        source_urn=SourceURN("URN:SRC:1880:US_PA:MEM_044"),
        record_type=SourceRecordType.LODGE_RECORD,
        description="St. John's Lodge No. 260 Membership Entry",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        individual_id=IndividualID("IND-000001"),
        organization_name_raw="St. John's Lodge No. 260, F. & A. M.",
        org_id=OrganizationID("ORG-000001"),
        org_category=OrganizationCategory.FRATERNAL,
        affiliation_type=AffiliationType.MEMBER,
        membership_status=MembershipStatus.ACTIVE,
        degree_or_rank_raw="Master Mason",
    )
    assert mem_mapper.from_row(mem_mapper.to_row(membership)) == membership

    ros_mapper = OrganizationRosterRecordMapper()
    roster = OrganizationRosterRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000045"),
        source_urn=SourceURN("URN:SRC:1885:US_PA:ROS_045"),
        record_type=SourceRecordType.MEMBERSHIP_ROSTER,
        description="Zion Lutheran Church Roll of Communicants",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        enumeration_year=HistoricalYear(1885),
        jurisdiction_raw="Carlisle, PA",
        jurisdiction_id=LocationID("LOC-000001"),
        organization_name_raw="Zion Lutheran Church",
        org_id=OrganizationID("ORG-000001"),
        org_category=OrganizationCategory.RELIGIOUS,
        roster_title="Roll of Communicants",
        entries=(
            OrganizationRosterEntry(
                entry_urn=SourceURN("URN:SRC:1885:US_PA:ROS_045_L1"),
                line_number=1,
                member_name_verbatim="John Lehman",
                individual_id=IndividualID("IND-000001"),
            ),
        ),
    )
    assert ros_mapper.from_row(ros_mapper.to_row(roster)) == roster

    misc_mapper = OtherMiscellaneousRecordMapper()
    misc = OtherMiscellaneousRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000046"),
        source_urn=SourceURN("URN:SRC:1892:US_PA:MSC_046"),
        record_type=SourceRecordType.RECEIPT,
        description="Blacksmith Shop Account Receipt",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        item_date=EventDate.from_dict("1892-07-14"),
        organization_or_entity_name="Lehman & Son Blacksmithing",
        organization_location_id=LocationID("LOC-000001"),
        custom_fields={"amount_usd": "4.25"},
    )
    assert misc_mapper.from_row(misc_mapper.to_row(misc)) == misc


def test_education_manuscripts_orgs_other_mapper_error_branches() -> None:
    """Verify EntityMappingError branches across all 6 Batch 4 mappers."""
    for mapper in (
        AcademicCredentialRecordMapper(),
        FamilyBibleRecordMapper(),
        NarrativeManuscriptRecordMapper(),
        OrganizationMembershipRecordMapper(),
        OrganizationRosterRecordMapper(),
        OtherMiscellaneousRecordMapper(),
    ):
        with pytest.raises(EntityMappingError):
            mapper.to_row(object())  # type: ignore[arg-type]

        with pytest.raises(EntityMappingError, match="Missing or invalid 'payload_json'"):
            mapper.from_row({"payload_json": ""})

        with pytest.raises(EntityMappingError, match="Failed to hydrate"):
            mapper.from_row({"payload_json": "{bad-json"})
