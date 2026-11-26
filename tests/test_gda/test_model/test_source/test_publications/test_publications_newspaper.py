"""Path: tests/test_gda/test_model/test_source/test_publications/test_publications_newspaper.py

Comprehensive unit tests for gda.model.source.publications.newspaper.NewspaperClipRecord.

Operational Role:
    Exercises factory creation, SourceRecord inheritance, category and record_type
    bounds, NEWS_CATEGORY_REGEX and PUB_CODE_REGEX enforcement, EventDate coercion,
    dict/JSON round-trip serialization, and defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.publications import NewspaperClipRecord

__version__ = "1.0.0+build.2"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_PARENT_SID = "44444444-4444-4444-8444-444444444444"
_MID = "33333333-3333-4333-8333-333333333333"
_URN = "URN:SRC:1942:US_NH_CONCORD:MONITOR_19421120_OBIT"
_URN_MIN = "URN:SRC:1894:US_NH_CONCORD:PATRIOT_18940615_MAR"


@pytest.mark.unit
@pytest.mark.smoke
def test_newspaper_clip_record_create_and_roundtrip() -> None:
    """Verify NewspaperClipRecord.create with full bibliographic fields and serialization."""
    now = IsoTimestamp("2026-06-02T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    issue_dt = EventDate.create("1942-11-20")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000001"),
        name_raw="John H. Abbott",
        role=AssociatedRole.DECEASED,
    )

    clip = NewspaperClipRecord.create(
        source_id=_SID,
        source_urn=_URN,
        description="Obituary of John H. Abbott in the Concord Daily Monitor.",
        repository_id="REP-000001",
        newspaper_name_raw="  Concord Daily Monitor  ",
        issue_date=issue_dt,
        news_category="  obituary  ",
        record_category="news",
        record_type="miscellaneous",
        parent_source_id=_PARENT_SID,
        pub_code="  concord_monitor  ",
        publication_location_raw="Concord, NH",
        publication_location_id="LOC-000001",
        headline_raw="JOHN H. ABBOTT DIES AT 75; LONG A MASTER CARPENTER",
        byline_raw="Special Correspondent",
        volume_issue="Vol. LXXVIII, No. 274",
        page_column="p. 6, col. 3",
        edition="Evening Edition",
        article_summary="Lists surviving widow Mary E. Colby and son Samuel H. Abbott.",
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert clip.newspaper_name_raw == "Concord Daily Monitor"
    assert clip.news_category == "OBITUARY"
    assert clip.pub_code == "CONCORD_MONITOR"
    assert clip.parent_source_id == SourceID(_PARENT_SID)
    assert clip.publication_location_id == LocationID("LOC-000001")
    assert str(clip) == "NewspaperClipRecord [Concord Daily Monitor - OBITUARY] (1942-11-20)"

    payload = clip.to_dict()
    assert payload["parent_source_id"] == _PARENT_SID
    assert payload["pub_code"] == "CONCORD_MONITOR"
    assert payload["headline_raw"] == "JOHN H. ABBOTT DIES AT 75; LONG A MASTER CARPENTER"

    restored = NewspaperClipRecord.from_dict(payload)
    assert restored == clip

    restored_json = NewspaperClipRecord.from_json(clip.to_json())
    assert restored_json == clip

    # Direct AuditStamp and EventDate objects passed in from_dict
    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["issue_date"] = issue_dt
    assert NewspaperClipRecord.from_dict(direct_payload) == clip


@pytest.mark.unit
@pytest.mark.integrity
def test_newspaper_clip_record_validation_and_minimal_roundtrip() -> None:
    """Verify NewspaperClipRecord minimal round-trip and validation error branches."""
    minimal = NewspaperClipRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_MIN,
        description="Marriage notice in New Hampshire Patriot.",
        repository_id=RepositoryID("REP-000001"),
        newspaper_name_raw="New Hampshire Patriot",
        issue_date="1894-06-15",
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "parent_source_id",
        "pub_code",
        "publication_location_raw",
        "publication_location_id",
        "headline_raw",
        "byline_raw",
        "volume_issue",
        "page_column",
        "edition",
        "article_summary",
    ):
        assert opt_key not in min_dict
    assert NewspaperClipRecord.from_dict(min_dict) == minimal

    # Direct constructor normalizes whitespace/case
    direct = NewspaperClipRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct init test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        newspaper_name_raw="  Trimmed Paper  ",
        issue_date=EventDate.create("1894-06-15"),
        news_category="  marriage  ",
        pub_code="  nh_patriot  ",
    )
    assert direct.newspaper_name_raw == "Trimmed Paper"
    assert direct.news_category == "MARRIAGE"
    assert direct.pub_code == "NH_PATRIOT"

    # Disallowed category / record_type
    with pytest.raises(ModelFormatError, match="requires record_category in"):
        NewspaperClipRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong category",
            repository_id="REP-000001",
            newspaper_name_raw="New Hampshire Patriot",
            issue_date="1894-06-15",
            record_category=SourceRecordCategory.CENSUS,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        NewspaperClipRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong type",
            repository_id="REP-000001",
            newspaper_name_raw="New Hampshire Patriot",
            issue_date="1894-06-15",
            record_type=SourceRecordType.BAPTISM_REGISTER,
        )

    # Empty masthead / invalid news_category / invalid pub_code / invalid date
    with pytest.raises(ModelFormatError, match="newspaper_name_raw"):
        NewspaperClipRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty paper",
            repository_id="REP-000001",
            newspaper_name_raw="   ",
            issue_date="1894-06-15",
        )

    with pytest.raises(ModelFormatError, match="Invalid news_category format"):
        NewspaperClipRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad news_category",
            repository_id="REP-000001",
            newspaper_name_raw="New Hampshire Patriot",
            issue_date="1894-06-15",
            news_category="OBIT_123",
        )

    with pytest.raises(ModelFormatError, match="Invalid pub_code format"):
        NewspaperClipRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad pub_code",
            repository_id="REP-000001",
            newspaper_name_raw="New Hampshire Patriot",
            issue_date="1894-06-15",
            pub_code="A",
        )

    with pytest.raises(ModelFormatError, match="Invalid 'issue_date' payload"):
        NewspaperClipRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad date",
            repository_id="REP-000001",
            newspaper_name_raw="New Hampshire Patriot",
            issue_date=18940615,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        NewspaperClipRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        NewspaperClipRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        NewspaperClipRecord.from_dict(bad_audit)
