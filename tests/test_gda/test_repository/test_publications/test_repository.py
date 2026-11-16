"""Path: tests/test_gda/test_repository/test_publications/test_repository.py

Unit and integration tests for Publications domain SQLite repositories
(src/gda/repository/publications/repository.py).
"""

from __future__ import annotations

from gda.core.enums.archival import PublicationFrequency
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    OrganizationID,
    RepositoryID,
    SourceID,
)
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.name import NameThing
from gda.model.source.publications import (
    NewspaperClipRecord,
    PeriodicalArticleRecord,
    Publication,
    PublicationEntry,
)
from gda.repository.publications.repository import (
    NewspaperClipRepository,
    PeriodicalArticleRepository,
    PublicationRepository,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_publications_repositories(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify PublicationRepository, NewspaperClipRepository, and PeriodicalArticleRepository."""
    pub_repo = PublicationRepository(session_manager=seeded_session)
    clip_repo = NewspaperClipRepository(session_manager=seeded_session)
    art_repo = PeriodicalArticleRepository(session_manager=seeded_session)

    pub = Publication(
        source_id=SourceID("00000000-0000-4000-8000-000000000016"),
        source_urn=SourceURN("URN:SRC:1850:US_PA:PUB_HERALD"),
        description="Carlisle Herald Master Entry",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        title=NameThing.create("The Carlisle Herald"),
        pub_code="PA-CARL-HERALD",
        frequency=PublicationFrequency.WEEKLY,
        location_id=LocationID("LOC-000001"),
        is_active=False,
    )
    pub_repo.upsert(pub)
    assert pub_repo.get_or_raise(pub.source_id) == pub
    assert pub_repo.get_by_pub_code("PA-CARL-HERALD") == pub
    assert pub_repo.get_by_pub_code("MISSING") is None
    assert len(pub_repo.find_by_location("LOC-000001")) == 1

    clip = NewspaperClipRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000017"),
        source_urn=SourceURN("URN:SRC:1922:US_PA:CLIP_OBIT_017"),
        record_type=SourceRecordType.MISC,
        description="Obituary of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        newspaper_name_raw="The Carlisle Herald",
        issue_date=EventDate.from_dict("1922-11-10"),
        news_category="OBITUARY",
        parent_source_id=pub.source_id,
        pub_code="PA-CARL-HERALD",
        publication_location_id=LocationID("LOC-000001"),
        headline_raw="Lifelong Resident Passes",
    )
    clip_repo.upsert(clip)
    assert clip_repo.get_or_raise(clip.source_id) == clip
    assert len(clip_repo.find_by_pub_code("PA-CARL-HERALD")) == 1
    assert len(clip_repo.find_by_parent_source(pub.source_id)) == 1
    assert len(clip_repo.find_by_location("LOC-000001")) == 1
    assert len(clip_repo.find_by_year_range(1920, 1925)) == 1

    article = PeriodicalArticleRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000018"),
        source_urn=SourceURN("URN:SRC:1915:US_PA:ART_ALUMNI_018"),
        record_category=SourceRecordCategory.EDUCATION,
        record_type=SourceRecordType.CLASS_ROSTER,
        description="Dickinson Alumni Quarterly Roster",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        publication_title_raw="Dickinson Alumni Quarterly",
        date_published=EventDate.from_dict("1915-06-01"),
        publication_kind="Alumni Magazine",
        parent_source_id=pub.source_id,
        pub_code="PA-DICKINSON-Q",
        institution_org_id=OrganizationID("ORG-000001"),
        entries=(
            PublicationEntry(
                line_number=1,
                subject_name_verbatim="John Lehman",
                individual_id=IndividualID("IND-000001"),
                role_or_class_raw="Class of 1874",
            ),
        ),
    )
    art_repo.upsert(article)
    assert art_repo.get_or_raise(article.source_id) == article
    assert len(art_repo.find_by_pub_code("PA-DICKINSON-Q")) == 1
    assert len(art_repo.find_by_parent_source(pub.source_id)) == 1
    assert len(art_repo.find_by_institution_org("ORG-000001")) == 1
    assert len(art_repo.find_by_year_range(1910, 1920)) == 1
