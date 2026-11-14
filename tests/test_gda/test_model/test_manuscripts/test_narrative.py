"""Path: tests/test_gda/test_model/test_manuscripts/test_narrative.py

Comprehensive unit tests for gda.model.manuscripts.narrative.NarrativeManuscriptRecord.

Operational Role:
    Exercises NarrativeManuscriptRecord creation, URN:MS, URN:NARRATIVE, and
    URN:SRC resolution, category and record_type bounds, dict/JSON round-trip
    serialization, and defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.manuscripts import NarrativeManuscriptRecord

__version__ = "1.0.0+build.1"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN_MS = "URN:MS:1863:US_NH_HIST:ABBOTT_LETTERS_B2_F4"
_URN_SRC = "URN:SRC:1896:US_NH_CONCORD:ABBOTT_FAMILY_MEMOIR"


@pytest.mark.unit
@pytest.mark.smoke
def test_narrative_manuscript_record_roundtrip() -> None:
    """Verify NarrativeManuscriptRecord full metadata and serialization."""
    now = IsoTimestamp("2026-11-03T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    written_dt = EventDate.create("1863-07-08")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000001"),
        name_raw="George W. Abbott",
        role=AssociatedRole.PRIMARY,
    )

    rec = NarrativeManuscriptRecord.create(
        source_id=_SID,
        source_urn=_URN_MS,
        description="Civil War letter from George W. Abbott near Gettysburg to Mary E. Abbott.",
        repository_id="REP-000001",
        title_or_subject="  Letter from Camp near Gettysburg, PA  ",
        record_category="manuscript",
        record_type="personal_letter",
        author_or_sender_raw="George W. Abbott",
        author_or_sender_id="IND-000001",
        recipient_raw="Mary E. Abbott",
        recipient_id="IND-000002",
        collection_name="Abbott Family Papers, 1840-1910",
        box_folder_or_page="Box 2, Folder 4",
        origin_place_raw="Gettysburg, PA",
        origin_place_id="LOC-000050",
        destination_place_raw="Concord, NH",
        destination_place_id="LOC-000001",
        date_written_or_published=written_dt,
        transcript_excerpt="Dear Wife, I take this opportunity after the late battle...",
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.title_or_subject == "Letter from Camp near Gettysburg, PA"
    assert rec.author_or_sender_id == IndividualID("IND-000001")
    assert rec.recipient_id == IndividualID("IND-000002")
    assert rec.origin_place_id == LocationID("LOC-000050")
    assert rec.destination_place_id == LocationID("LOC-000001")
    assert (
        str(rec)
        == "NarrativeManuscriptRecord [PERSONAL_LETTER] Letter from Camp near Gettysburg, PA"
    )

    payload = rec.to_dict()
    assert payload["collection_name"] == "Abbott Family Papers, 1840-1910"

    restored = NarrativeManuscriptRecord.from_dict(payload)
    assert restored == rec

    restored_json = NarrativeManuscriptRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct ArchivalURN, AuditStamp, and EventDate instances
    direct_urn_rec = NarrativeManuscriptRecord.create(
        source_id=_SID,
        source_urn=ArchivalURN(_URN_MS),
        description="Direct ArchivalURN instance check.",
        repository_id="REP-000001",
        title_or_subject="Letter from Camp near Gettysburg, PA",
    )
    assert direct_urn_rec.source_urn == ArchivalURN(_URN_MS)

    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["date_written_or_published"] = written_dt
    assert NarrativeManuscriptRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_narrative_manuscript_validation_and_minimal_roundtrip() -> None:
    """Verify NarrativeManuscriptRecord minimal round-trip and validation error branches."""
    minimal = NarrativeManuscriptRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_SRC,
        description="Reminiscences of Early Concord by Samuel H. Abbott.",
        repository_id=RepositoryID("REP-000001"),
        title_or_subject="Reminiscences of Early Concord",
        record_category=SourceRecordCategory.NARRATIVE,
        record_type=SourceRecordType.MEMOIR,
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "author_or_sender_raw",
        "author_or_sender_id",
        "recipient_raw",
        "recipient_id",
        "collection_name",
        "box_folder_or_page",
        "origin_place_raw",
        "origin_place_id",
        "destination_place_raw",
        "destination_place_id",
        "date_written_or_published",
        "transcript_excerpt",
    ):
        assert opt_key not in min_dict
    assert NarrativeManuscriptRecord.from_dict(min_dict) == minimal

    # String date coercion & direct constructor whitespace trim
    str_dt = NarrativeManuscriptRecord.create(
        source_id=_SID,
        source_urn=_URN_SRC,
        description="String date check",
        repository_id="REP-000001",
        title_or_subject="Diary of Samuel Abbott",
        date_written_or_published="1871-01-01",
    )
    assert str_dt.date_written_or_published == EventDate.create("1871-01-01")

    direct = NarrativeManuscriptRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        title_or_subject="  Trimmed Title  ",
    )
    assert direct.title_or_subject == "Trimmed Title"

    # Validation branches
    with pytest.raises(ModelFormatError, match="Invalid Manuscript/Narrative URN syntax"):
        NarrativeManuscriptRecord.create(
            source_id=_SID,
            source_urn="URN:NARRATIVE:bad",
            description="Bad URN",
            repository_id="REP-000001",
            title_or_subject="Title",
        )

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        NarrativeManuscriptRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong category",
            repository_id="REP-000001",
            title_or_subject="Title",
            record_category=SourceRecordCategory.CENSUS,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        NarrativeManuscriptRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong type",
            repository_id="REP-000001",
            title_or_subject="Title",
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="title_or_subject"):
        NarrativeManuscriptRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Empty title",
            repository_id="REP-000001",
            title_or_subject="   ",
        )

    with pytest.raises(ModelFormatError, match="Invalid 'date_written_or_published' payload"):
        NarrativeManuscriptRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad date",
            repository_id="REP-000001",
            title_or_subject="Title",
            date_written_or_published=1863,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        NarrativeManuscriptRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        NarrativeManuscriptRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        NarrativeManuscriptRecord.from_dict(bad_audit)
