"""Path: tests/test_gda/test_repository/test_publications/test_collection.py

Unit and integration tests for Publications domain collections
(src/gda/repository/publications/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from gda.core.enums.archival import PublicationFrequency
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, OrganizationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.name import NameThing
from gda.model.source.publications import (
    NewspaperClipRecord,
    PeriodicalArticleRecord,
    Publication,
)
from gda.repository.publications.collection import (
    NewspaperClipCollection,
    PeriodicalArticleCollection,
    PublicationCollection,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_publications_collections_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and JSON round-tripping across all 3 Publications collections."""
    # 1. PublicationCollection
    pub_coll = PublicationCollection.from_database(seeded_session)
    pub = Publication(
        source_id=SourceID("00000000-0000-4000-8000-000000000211"),
        source_urn=SourceURN("URN:SRC:1850:US_PA:PUB211"),
        description="Herald",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        title=NameThing.create("The Carlisle Herald"),
        pub_code="PA-HERALD",
        frequency=PublicationFrequency.WEEKLY,
        location_id=LocationID("LOC-000001"),
    )
    pub_coll.add(pub)
    assert pub_coll.get_by_pub_code("PA-HERALD") == pub
    assert pub_coll.get_by_pub_code("NONE") is None
    assert len(pub_coll.find_by_location("LOC-000001")) == 1
    pub_coll.edit(pub.source_id, location_id=None)
    assert len(pub_coll.find_by_location("LOC-000001")) == 0
    pub_coll.edit(pub.source_id, description="Pub None Branch")
    pub_coll.add(
        dataclasses.replace(
            pub,
            source_id=SourceID("00000000-0000-4000-8000-000000000311"),
            source_urn=SourceURN("URN:SRC:1850:US_PA:PUB311"),
            pub_code="PA-HERALD-2",
            location_id=None,
        )
    )
    p_pub = tmp_path / "pub.json"
    pub_coll.export_file(p_pub)
    PublicationCollection().import_file(p_pub)

    # 2. NewspaperClipCollection
    clip_coll = NewspaperClipCollection.from_database(seeded_session)
    clip = NewspaperClipRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000212"),
        source_urn=SourceURN("URN:SRC:1922:US_PA:CLIP212"),
        record_type=SourceRecordType.MISC,
        description="Clip",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        newspaper_name_raw="Herald",
        issue_date=EventDate.from_dict("1922-11-10"),
        news_category="OBITUARY",
        parent_source_id=pub.source_id,
        pub_code="PA-HERALD",
    )
    clip_coll.add(clip)
    assert len(clip_coll.find_by_pub_code("PA-HERALD")) == 1
    assert len(clip_coll.find_by_parent_source(pub.source_id)) == 1
    clip_coll.edit(clip.source_id, pub_code=None, parent_source_id=None)
    assert len(clip_coll.find_by_pub_code("PA-HERALD")) == 0
    clip_coll.edit(clip.source_id, description="Clip None Branch")
    clip_coll.add(
        dataclasses.replace(
            clip,
            source_id=SourceID("00000000-0000-4000-8000-000000000312"),
            source_urn=SourceURN("URN:SRC:1922:US_PA:CLIP312"),
            pub_code=None,
            parent_source_id=None,
        )
    )
    p_clip = tmp_path / "clip.json"
    clip_coll.export_file(p_clip)
    NewspaperClipCollection().import_file(p_clip)

    # 3. PeriodicalArticleCollection
    art_coll = PeriodicalArticleCollection.from_database(seeded_session)
    art = PeriodicalArticleRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000213"),
        source_urn=SourceURN("URN:SRC:1915:US_PA:ART213"),
        record_category=SourceRecordCategory.EDUCATION,
        record_type=SourceRecordType.CLASS_ROSTER,
        description="Roster",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        publication_title_raw="Alumni",
        date_published=EventDate.from_dict("1915-06-01"),
        publication_kind="Alumni",
        pub_code="PA-DICKINSON",
        institution_org_id=OrganizationID("ORG-000001"),
    )
    art_coll.add(art)
    assert len(art_coll.find_by_pub_code("PA-DICKINSON")) == 1
    assert len(art_coll.find_by_institution_org("ORG-000001")) == 1
    art_coll.edit(art.source_id, pub_code=None, institution_org_id=None)
    assert len(art_coll.find_by_pub_code("PA-DICKINSON")) == 0
    art_coll.edit(art.source_id, description="Art None Branch")
    art_coll.add(
        dataclasses.replace(
            art,
            source_id=SourceID("00000000-0000-4000-8000-000000000313"),
            source_urn=SourceURN("URN:SRC:1915:US_PA:ART313"),
            pub_code=None,
            institution_org_id=None,
        )
    )
    p_art = tmp_path / "art.json"
    art_coll.export_file(p_art)
    PeriodicalArticleCollection().import_file(p_art)
