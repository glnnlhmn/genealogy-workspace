"""Path: tests/test_gda/test_model/test_manuscripts/test_bible.py

Comprehensive unit tests for gda.model.manuscripts.bible
(FamilyBibleRecord and BibleRegisterEntry).

Operational Role:
    Exercises BibleRegisterEntry and FamilyBibleRecord creation, URN:MS,
    URN:BIBLE, and URN:SRC resolution, FactType event bounds, duplicate line
    prevention, flatten_entries() tabular projection, dict/JSON round-trip
    serialization, and defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole, FactType
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.manuscripts import BibleRegisterEntry, FamilyBibleRecord

__version__ = "1.0.0+build.1"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN_BIBLE = "URN:BIBLE:1842:US_NH_MERRIMACK:ABBOTT_FAMILY_BIBLE"
_URN_SRC = "URN:SRC:1855:US_NH_MERRIMACK:KIMBALL_BIBLE_REG"


@pytest.mark.unit
@pytest.mark.smoke
def test_bible_entry_and_record_roundtrip() -> None:
    """Verify BibleRegisterEntry and FamilyBibleRecord full metadata and serialization."""
    now = IsoTimestamp("2026-11-02T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    b_dt = EventDate.create("1844-05-12")
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

    e1 = BibleRegisterEntry.create(
        line_number=1,
        subject_name_raw="  George W. Abbott  ",
        event_type="birth",
        subject_id="IND-000001",
        secondary_name_raw="Samuel H. Abbott & Hannah Kimball",
        secondary_id="IND-000002",
        event_date=b_dt,
        place_raw="Concord, NH",
        place_id="LOC-000001",
        transcription_raw="George Washington Abbott born May 12th 1844",
    )
    e2 = BibleRegisterEntry.create(
        line_number=2,
        subject_name_raw="George W. Abbott & Mary E. Rolfe",
        event_type=FactType.MARRIAGE,
    )

    assert e1.subject_name_raw == "George W. Abbott"
    assert e1.event_type is FactType.BIRTH
    assert e2.event_type is FactType.MARRIAGE
    assert str(e1) == "Line 1 [BIRTH]: George W. Abbott"
    assert BibleRegisterEntry.from_json(e1.to_json()) == e1

    e2_dict = e2.to_dict()
    for opt_key in (
        "subject_id",
        "secondary_name_raw",
        "secondary_id",
        "event_date",
        "place_raw",
        "place_id",
        "transcription_raw",
    ):
        assert opt_key not in e2_dict
    assert BibleRegisterEntry.from_dict(e2_dict) == e2

    rec = FamilyBibleRecord.create(
        source_id=_SID,
        source_urn=_URN_BIBLE,
        description="Abbott Family Bible Vital Register pages.",
        repository_id="REP-000001",
        family_surname="  Abbott  ",
        record_category="manuscript",
        record_type="bible",
        edition_imprint="Philadelphia: Jesper Harding, 1842",
        publication_year=1842,
        original_owner_raw="Samuel H. Abbott",
        original_owner_id="IND-000002",
        custodian_or_provenance="New Hampshire Historical Society Manuscript Vault",
        entries=[e1, e2],
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.family_surname == "Abbott"
    assert rec.publication_year == 1842
    assert rec.original_owner_id == IndividualID("IND-000002")
    assert rec.entry_count == 2
    assert str(rec) == "FamilyBibleRecord [Abbott] (2 entries)"

    flat = rec.flatten_entries()
    assert len(flat) == 2
    assert flat[0]["subject_name_raw"] == "George W. Abbott"
    assert flat[0]["family_surname"] == "Abbott"

    payload = rec.to_dict()
    assert payload["publication_year"] == 1842
    assert len(payload["entries"]) == 2

    restored = FamilyBibleRecord.from_dict(payload)
    assert restored == rec

    restored_json = FamilyBibleRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct ArchivalURN, AuditStamp, and BibleRegisterEntry instances
    direct_urn_rec = FamilyBibleRecord.create(
        source_id=_SID,
        source_urn=ArchivalURN(_URN_BIBLE),
        description="Direct ArchivalURN instance check.",
        repository_id="REP-000001",
        family_surname="Abbott",
    )
    assert direct_urn_rec.source_urn == ArchivalURN(_URN_BIBLE)

    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["entries"] = [e1, e2]
    assert FamilyBibleRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_bible_validation_and_minimal_roundtrip() -> None:
    """Verify FamilyBibleRecord minimal round-trip and validation error branches."""
    minimal = FamilyBibleRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_SRC,
        description="Kimball Family Bible Register.",
        repository_id=RepositoryID("REP-000001"),
        family_surname="Kimball",
        record_category=SourceRecordCategory.VITAL,
        record_type=SourceRecordType.BIBLE,
        media_ids=[MediaID(_MID)],
    )
    assert minimal.entry_count == 0
    min_dict = minimal.to_dict()
    for opt_key in (
        "edition_imprint",
        "publication_year",
        "original_owner_raw",
        "original_owner_id",
        "custodian_or_provenance",
    ):
        assert opt_key not in min_dict
    assert FamilyBibleRecord.from_dict(min_dict) == minimal

    # Direct constructors normalize whitespace
    direct_e = BibleRegisterEntry(line_number=1, subject_name_raw="  Hannah Kimball  ")
    assert direct_e.subject_name_raw == "Hannah Kimball"

    direct_rec = FamilyBibleRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        family_surname="  Trimmed Surname  ",
    )
    assert direct_rec.family_surname == "Trimmed Surname"

    # BibleRegisterEntry error branches
    with pytest.raises(ModelFormatError, match="subject_name_raw"):
        BibleRegisterEntry.create(line_number=1, subject_name_raw="   ")

    with pytest.raises(ModelFormatError, match="Invalid FactType value"):
        BibleRegisterEntry.create(line_number=1, subject_name_raw="Test", event_type="INVALID")

    with pytest.raises(ModelFormatError, match="BibleRegisterEntry event_type must be in"):
        BibleRegisterEntry.create(
            line_number=1, subject_name_raw="Test", event_type=FactType.CENSUS
        )

    with pytest.raises(ModelFormatError, match="BibleRegisterEntry event_type must be in"):
        BibleRegisterEntry(line_number=1, subject_name_raw="Test", event_type=FactType.CENSUS)

    with pytest.raises(ModelFormatError, match="Invalid 'event_date' payload"):
        BibleRegisterEntry.create(
            line_number=1,
            subject_name_raw="Test",
            event_date=1844,  # type: ignore[arg-type]
        )

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        BibleRegisterEntry.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'line_number'"):
        BibleRegisterEntry.from_dict({"line_number": 1})

    with pytest.raises(ModelFormatError, match="Failed to parse BibleRegisterEntry JSON"):
        BibleRegisterEntry.from_json("{bad-json")

    # FamilyBibleRecord validation branches
    with pytest.raises(ModelFormatError, match="Invalid Manuscript/Bible URN syntax"):
        FamilyBibleRecord.create(
            source_id=_SID,
            source_urn="URN:BIBLE:bad",
            description="Bad URN",
            repository_id="REP-000001",
            family_surname="Abbott",
        )

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        FamilyBibleRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong category",
            repository_id="REP-000001",
            family_surname="Abbott",
            record_category=SourceRecordCategory.CENSUS,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        FamilyBibleRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong type",
            repository_id="REP-000001",
            family_surname="Abbott",
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="family_surname"):
        FamilyBibleRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Empty surname",
            repository_id="REP-000001",
            family_surname="   ",
        )

    with pytest.raises(ModelFormatError, match="Duplicate BibleRegisterEntry line_number"):
        FamilyBibleRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Duplicate lines",
            repository_id="REP-000001",
            family_surname="Abbott",
            entries=[
                {"line_number": 1, "subject_name_raw": "A"},
                {"line_number": 1, "subject_name_raw": "B"},
            ],
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        FamilyBibleRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        FamilyBibleRecord.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        FamilyBibleRecord.from_dict(bad_audit)

    bad_entries = dict(min_dict)
    bad_entries["entries"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'entries' must be a list or tuple"):
        FamilyBibleRecord.from_dict(bad_entries)
