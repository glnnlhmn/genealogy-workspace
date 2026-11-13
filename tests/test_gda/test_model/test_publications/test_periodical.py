"""Path: tests/test_gda/test_model/test_publications/test_periodical.py

Comprehensive unit tests for gda.model.publications.periodical
(PeriodicalArticleRecord and PublicationEntry).

Operational Role:
    Exercises PublicationEntry creation, serialization, and validation;
    PeriodicalArticleRecord creation, category/record_type bounds, PUB_CODE_REGEX,
    duplicate line_number prevention, flatten_entries() tabular projection,
    dict/JSON round-trip serialization, and defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.sources import EducationLevel, SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, MediaID, OrganizationID, RepositoryID, SourceID
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.publications import PeriodicalArticleRecord, PublicationEntry

__version__ = "1.0.0+build.1"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_PARENT_SID = "44444444-4444-4444-8444-444444444444"
_MID = "33333333-3333-4333-8333-333333333333"
_URN = "URN:SRC:1918:US_NH_CONCORD:CHS_YEARBOOK_1918_P24"
_URN_MIN = "URN:SRC:1885:US_NH_MERRIMACK:COUNTY_HIST_P412"


@pytest.mark.unit
@pytest.mark.smoke
def test_publication_entry_and_periodical_roundtrip() -> None:
    """Verify PublicationEntry and PeriodicalArticleRecord full serialization and flattening."""
    now = IsoTimestamp("2026-06-03T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    pub_date = EventDate.create("1918")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000001"),
        name_raw="Samuel H. Abbott",
        role=AssociatedRole.PRIMARY,
    )

    e1 = PublicationEntry.create(
        line_number=1,
        subject_name_verbatim="  Samuel H. Abbott  ",
        individual_id="IND-000001",
        role_or_class_raw="Senior Class President",
        page_or_plate="p. 24, top left",
        remarks_raw="Classical Course; Debating Society",
    )
    e2 = PublicationEntry.create(
        line_number=2,
        subject_name_verbatim="Ruth E. Colby",
    )

    assert e1.subject_name_verbatim == "Samuel H. Abbott"
    assert str(e1) == "Line 1: Samuel H. Abbott"
    assert PublicationEntry.from_json(e1.to_json()) == e1

    e2_dict = e2.to_dict()
    for opt_key in ("individual_id", "role_or_class_raw", "page_or_plate", "remarks_raw"):
        assert opt_key not in e2_dict
    assert PublicationEntry.from_dict(e2_dict) == e2

    rec = PeriodicalArticleRecord.create(
        source_id=_SID,
        source_urn=_URN,
        description="Concord High School 1918 Yearbook Senior Portraits Page 24.",
        repository_id="REP-000001",
        publication_title_raw="  The Concordian (1918)  ",
        date_published=pub_date,
        publication_kind="  yearbook  ",
        record_category="education",
        record_type="yearbook_page",
        parent_source_id=_PARENT_SID,
        pub_code="  chs_concordian  ",
        institution_or_publisher_raw="Concord High School",
        institution_org_id="ORG-000020",
        author_or_editor_raw="Class of 1918 Editorial Board",
        article_or_chapter_title="Senior Class Biographies",
        volume_issue="Vol. XII",
        page_or_plate="p. 24",
        education_level="hs",
        entries=[e1, e2],
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.publication_title_raw == "The Concordian (1918)"
    assert rec.publication_kind == "YEARBOOK"
    assert rec.pub_code == "CHS_CONCORDIAN"
    assert rec.parent_source_id == SourceID(_PARENT_SID)
    assert rec.institution_org_id == OrganizationID("ORG-000020")
    assert rec.education_level is EducationLevel.HS
    assert rec.entry_count == 2
    assert str(rec) == "PeriodicalArticleRecord [The Concordian (1918)] (1918)"

    flat = rec.flatten_entries()
    assert len(flat) == 2
    assert flat[0]["subject_name_verbatim"] == "Samuel H. Abbott"
    assert flat[0]["publication_title_raw"] == "The Concordian (1918)"
    assert flat[1]["subject_name_verbatim"] == "Ruth E. Colby"

    payload = rec.to_dict()
    assert payload["education_level"] == "HS"
    assert len(payload["entries"]) == 2

    restored = PeriodicalArticleRecord.from_dict(payload)
    assert restored == rec

    restored_json = PeriodicalArticleRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct AuditStamp, EventDate, and PublicationEntry instances in from_dict
    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["date_published"] = pub_date
    direct_payload["entries"] = [e1, e2]
    assert PeriodicalArticleRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_periodical_validation_and_minimal_roundtrip() -> None:
    """Verify PeriodicalArticleRecord minimal round-trip and validation error branches."""
    minimal = PeriodicalArticleRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_MIN,
        description="History of Merrimack and Belknap Counties biographical sketch.",
        repository_id=RepositoryID("REP-000001"),
        publication_title_raw="History of Merrimack and Belknap Counties, New Hampshire",
        date_published="1885",
        record_category=SourceRecordCategory.NARRATIVE,
        record_type=SourceRecordType.MEMOIR,
        media_ids=[MediaID(_MID)],
    )
    assert minimal.entry_count == 0
    assert minimal.flatten_entries() == ()

    min_dict = minimal.to_dict()
    for opt_key in (
        "parent_source_id",
        "pub_code",
        "institution_or_publisher_raw",
        "institution_org_id",
        "author_or_editor_raw",
        "article_or_chapter_title",
        "volume_issue",
        "page_or_plate",
        "education_level",
    ):
        assert opt_key not in min_dict
    assert PeriodicalArticleRecord.from_dict(min_dict) == minimal

    # Direct constructor normalizes whitespace/case
    direct = PeriodicalArticleRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct init test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        publication_title_raw="  Trimmed Title  ",
        date_published=EventDate.create("1885"),
        publication_kind="  county_history  ",
        pub_code="  merr_hist  ",
    )
    assert direct.publication_title_raw == "Trimmed Title"
    assert direct.publication_kind == "COUNTY_HISTORY"
    assert direct.pub_code == "MERR_HIST"

    # PublicationEntry error branches
    with pytest.raises(ModelFormatError, match="subject_name_verbatim"):
        PublicationEntry.create(line_number=1, subject_name_verbatim="   ")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        PublicationEntry.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'line_number'"):
        PublicationEntry.from_dict({"line_number": 1})

    with pytest.raises(ModelFormatError, match="Failed to parse PublicationEntry JSON"):
        PublicationEntry.from_json("{not-json")

    # PeriodicalArticleRecord validation branches
    with pytest.raises(ModelFormatError, match="requires record_category in"):
        PeriodicalArticleRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong category",
            repository_id="REP-000001",
            publication_title_raw="Title",
            date_published="1885",
            record_category=SourceRecordCategory.TAX,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        PeriodicalArticleRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong type",
            repository_id="REP-000001",
            publication_title_raw="Title",
            date_published="1885",
            record_type=SourceRecordType.DEATH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="publication_title_raw"):
        PeriodicalArticleRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty title",
            repository_id="REP-000001",
            publication_title_raw="   ",
            date_published="1885",
        )

    with pytest.raises(ModelFormatError, match="publication_kind"):
        PeriodicalArticleRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty kind",
            repository_id="REP-000001",
            publication_title_raw="Title",
            date_published="1885",
            publication_kind="   ",
        )

    with pytest.raises(ModelFormatError, match="Invalid pub_code format"):
        PeriodicalArticleRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad pub_code",
            repository_id="REP-000001",
            publication_title_raw="Title",
            date_published="1885",
            pub_code="X",
        )

    with pytest.raises(ModelFormatError, match="Duplicate PublicationEntry line_number"):
        PeriodicalArticleRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Duplicate lines",
            repository_id="REP-000001",
            publication_title_raw="Title",
            date_published="1885",
            entries=[
                PublicationEntry.create(line_number=1, subject_name_verbatim="Person A"),
                PublicationEntry.create(line_number=1, subject_name_verbatim="Person B"),
            ],
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_published' payload"):
        PeriodicalArticleRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad date",
            repository_id="REP-000001",
            publication_title_raw="Title",
            date_published=1885,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        PeriodicalArticleRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        PeriodicalArticleRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        PeriodicalArticleRecord.from_dict(bad_audit)

    bad_entries = dict(min_dict)
    bad_entries["entries"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'entries' must be a list or tuple"):
        PeriodicalArticleRecord.from_dict(bad_entries)
