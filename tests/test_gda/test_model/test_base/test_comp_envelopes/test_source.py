"""Path: tests/test_gda/test_model/test_base/test_comp_envelopes/test_source.py

Comprehensive test suite verifying SourceReference, RecordMetadata, and SourceRecord.

Operational Role:
    Verifies evidentiary source composites, citation references, metadata headers,
    factory instantiation, copy-on-write mutators, dictionary/JSON serialization
    round trips, defensive error handling, and frozen immutability with 100%
    statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.enums.core import AssociatedRole
from gda.core.enums.sources import SourceRecordCategory
from gda.core.errors import ModelFormatError
from gda.model.atom.id import RepositoryID, SourceID
from gda.model.atom.scalar import ConfidenceScore, QuayScore
from gda.model.atom.urn import SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.source import RecordMetadata, SourceRecord, SourceReference
from gda.model.base.tombstone import Tombstone

__version__ = "1.1.0+build.1"


# ==============================================================================
# GROUP 1: SOURCEREFERENCE BEHAVIORS, FACTORY & MUTATORS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_source_reference_factory_and_defaults(golden_guid: str) -> None:
    """Verify SourceReference factory constructor, defaults, and string formatting."""
    ref = SourceReference.create(
        citation_text="1880 US Census, Merrimack County, NH",
        source_id=golden_guid,
        page_or_side="Folio 12B",
        quay=3,
        confidence=0.95,
    )
    assert ref.citation_text == "1880 US Census, Merrimack County, NH"
    assert ref.source_id == SourceID(golden_guid)
    assert ref.page_or_side == "Folio 12B"
    assert ref.quay == QuayScore(3)
    assert ref.confidence == ConfidenceScore(0.95)
    assert str(ref) == "1880 US Census, Merrimack County, NH (p. Folio 12B)"
    assert "Folio 12B" in repr(ref)

    minimal = SourceReference.create("Family Bible Records")
    assert str(minimal) == "Family Bible Records"
    assert minimal.source_id is None
    assert minimal.page_or_side is None


@pytest.mark.unit
def test_source_reference_copy_on_write_mutators() -> None:
    """Verify SourceReference copy-on-write mutators and idempotent no-op returns."""
    original = SourceReference.create("Original Citation", page_or_side="p. 10")

    up_text = original.update_citation("Updated Citation")
    assert up_text is not original
    assert up_text.citation_text == "Updated Citation"
    assert up_text.update_citation("Updated Citation") is up_text

    sid = SourceID("00000000-0000-4000-8000-000000000001")
    up_sid = original.update_source_id(sid)
    assert up_sid is not original
    assert up_sid.source_id == sid
    assert up_sid.update_source_id(sid) is up_sid
    assert up_sid.update_source_id(None).source_id is None

    up_page = original.update_page_or_side("p. 20")
    assert up_page is not original
    assert up_page.page_or_side == "p. 20"
    assert up_page.update_page_or_side("p. 20") is up_page
    assert up_page.update_page_or_side(None).page_or_side is None

    up_quay = original.update_quay(2)
    assert up_quay is not original
    assert up_quay.quay == QuayScore(2)
    assert up_quay.update_quay(2) is up_quay
    assert up_quay.update_quay(None).quay is None

    up_conf = original.update_confidence(0.85)
    assert up_conf is not original
    assert up_conf.confidence == ConfidenceScore(0.85)
    assert up_conf.update_confidence(0.85) is up_conf
    assert up_conf.update_confidence(None).confidence is None


@pytest.mark.unit
def test_source_reference_serialization_round_trip(golden_guid: str) -> None:
    """Verify SourceReference dictionary and JSON serialization round trip."""
    ref = SourceReference.create(
        citation_text="Town Records, Vol. 1",
        source_id=golden_guid,
        page_or_side="p. 45",
        quay=2,
        confidence=0.9,
    )
    data = ref.to_dict()
    assert data == {
        "citation_text": "Town Records, Vol. 1",
        "source_id": golden_guid,
        "page_or_side": "p. 45",
        "quay": 2,
        "confidence": 0.9,
    }
    assert SourceReference.from_dict(data) == ref
    assert SourceReference.from_json(ref.to_json()) == ref

    minimal = SourceReference.create("Bible Record")
    assert minimal.to_dict() == {"citation_text": "Bible Record"}


@pytest.mark.unit
@pytest.mark.regression
def test_source_reference_defensive_errors(golden_guid: str) -> None:
    """Verify SourceReference defensive validations, strict mode, and rejections."""
    with pytest.raises(ModelFormatError, match="citation_text cannot be empty"):
        SourceReference(citation_text="")

    with pytest.raises(ModelFormatError, match="page_or_side cannot be blank"):
        SourceReference(citation_text="Valid", page_or_side="   ")

    with pytest.raises(ModelFormatError, match="citation_text cannot be empty"):
        SourceReference.create("   ")

    with pytest.raises(ModelFormatError, match="citation_text cannot be empty"):
        SourceReference.create("Valid").update_citation("   ")

    with pytest.raises(ValidationError):
        SourceReference(citation_text=123)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        SourceReference.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'citation_text'"):
        SourceReference.from_dict({"source_id": golden_guid})

    with pytest.raises(ModelFormatError, match="Failed to parse SourceReference JSON string"):
        SourceReference.from_json("{broken-json")


# ==============================================================================
# GROUP 2: RECORDMETADATA BEHAVIORS & VALIDATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_record_metadata_factory_and_serialization(golden_guid: str) -> None:
    """Verify RecordMetadata factory instantiation, string formatting, and serialization."""
    meta = RecordMetadata.create(
        source_id=golden_guid,
        source_urn="urn:gda:doc:census:1880",
        record_category="CENSUS",
        record_type="POPULATION",
        repository_id="REP-000001",
    )
    assert meta.source_id == SourceID(golden_guid)
    assert meta.repository_id == RepositoryID("REP-000001")
    assert str(meta) == "RecordMetadata [CENSUS/POPULATION] urn:gda:doc:census:1880"
    assert "RecordMetadata" in repr(meta)

    data = meta.to_dict()
    assert data["repository_id"] == "REP-000001"
    assert RecordMetadata.from_dict(data) == meta
    assert RecordMetadata.from_json(meta.to_json()) == meta

    meta_no_repo = RecordMetadata.create(
        source_id=golden_guid,
        source_urn="urn:gda:doc:probate:1850",
        record_category="PROBATE",
        record_type="WILL",
    )
    assert "repository_id" not in meta_no_repo.to_dict()
    assert RecordMetadata.from_dict(meta_no_repo.to_dict()) == meta_no_repo


@pytest.mark.unit
@pytest.mark.regression
def test_record_metadata_defensive_errors(golden_guid: str) -> None:
    """Verify RecordMetadata boundary validations and rejections."""
    sid = SourceID(golden_guid)

    with pytest.raises(ValidationError):
        RecordMetadata(
            source_id="invalid-type",  # type: ignore[arg-type]
            source_urn="urn:test",
            record_category="TEST",
            record_type="TEST",
        )

    with pytest.raises(ModelFormatError, match="source_urn.*cannot be empty"):
        RecordMetadata(
            source_id=sid,
            source_urn="  ",
            record_category="TEST",
            record_type="TEST",
        )

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        RecordMetadata.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id, source_urn"):
        RecordMetadata.from_dict({"source_id": "abc"})

    with pytest.raises(ModelFormatError, match="Failed to parse RecordMetadata JSON string"):
        RecordMetadata.from_json("{broken-json")


# ==============================================================================
# GROUP 3: SOURCERECORD COMPOSITE TESTS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_source_record_factory_and_properties(
    golden_guid: str,
    golden_audit: AuditStamp,
    sample_source_urn: SourceURN,
) -> None:
    """Verify SourceRecord instantiation, properties, and string representation."""
    assoc = AssociatedIndividual.create(
        individual_id="IND-000001",
        role=AssociatedRole.INFORMANT,
        comment="Primary informant",
    )
    record = SourceRecord.create(
        source_id=golden_guid,
        source_urn=sample_source_urn,
        record_category="census",
        description="1880 Federal Population Schedule for Bow",
        repository_id="REP-000001",
        audit=golden_audit,
        media_ids=["f0000000-0000-4000-8000-000000000001"],
        associated_people=[assoc],
    )

    assert record.is_deprecated is False
    assert record.media_count == 1
    assert record.participant_count == 1
    assert "SourceRecord [CENSUS]" in str(record)
    assert "SourceRecord(" in repr(record)


@pytest.mark.unit
def test_source_record_serialization_round_trip(
    golden_guid: str,
    golden_audit: AuditStamp,
    sample_source_urn: SourceURN,
) -> None:
    """Verify SourceRecord dictionary and JSON serialization with and without tombstone."""
    sup_id = SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8e")
    record = SourceRecord.create(
        source_id=golden_guid,
        source_urn=sample_source_urn,
        record_category=SourceRecordCategory.VITAL,
        description="Birth Certificate entry",
        repository_id="REP-000002",
        audit=golden_audit,
        tombstone=Tombstone[SourceID](
            is_deprecated=True,
            deprecated_at=golden_audit.created_at,
            superseded_by=sup_id,
        ),
    )
    assert record.is_deprecated is True

    data = record.to_dict()
    assert data["record_category"] == "VITAL"
    assert data["tombstone"]["is_deprecated"] is True
    assert data["tombstone"]["superseded_by"] == str(sup_id)

    restored = SourceRecord.from_dict(data)
    assert restored == record
    assert SourceRecord.from_json(record.to_json()) == record

    # AuditStamp object intake in from_dict + omitted tombstone
    no_tombstone = SourceRecord.create(
        source_id=golden_guid,
        source_urn=sample_source_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Draft Card",
        repository_id="REP-000001",
    )
    no_tomb_data = no_tombstone.to_dict()
    assert "tombstone" not in no_tomb_data
    no_tomb_data["audit"] = no_tombstone.audit
    assert SourceRecord.from_dict(no_tomb_data) == no_tombstone


@pytest.mark.unit
@pytest.mark.regression
def test_source_record_defensive_errors(
    golden_guid: str,
    golden_audit: AuditStamp,
    sample_source_urn: SourceURN,
) -> None:
    """Verify SourceRecord boundary validations, strict mode, and error branches."""
    sid = SourceID(golden_guid)
    rep = RepositoryID("REP-000001")

    with pytest.raises(ModelFormatError, match="description.*cannot be empty"):
        SourceRecord(
            source_id=sid,
            source_urn=sample_source_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="   ",
            repository_id=rep,
            audit=golden_audit,
        )

    with pytest.raises(ModelFormatError, match="description.*cannot be empty"):
        SourceRecord.create(
            source_id=sid,
            source_urn=sample_source_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="   ",
            repository_id=rep,
        )

    with pytest.raises(ModelFormatError, match="Invalid SourceRecordCategory value"):
        SourceRecord.create(
            source_id=sid,
            source_urn=sample_source_urn,
            record_category="BAD_CAT",
            description="Valid",
            repository_id=rep,
        )

    with pytest.raises(ModelFormatError, match="Invalid SourceRecordCategory type"):
        SourceRecord.create(
            source_id=sid,
            source_urn=sample_source_urn,
            record_category=123,  # type: ignore[arg-type]
            description="Valid",
            repository_id=rep,
        )

    with pytest.raises(ValidationError):
        SourceRecord(
            source_id=sid,
            source_urn="not-an-archival-urn",  # type: ignore[arg-type]
            record_category=SourceRecordCategory.CENSUS,
            description="Valid",
            repository_id=rep,
            audit=golden_audit,
        )

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        SourceRecord.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id, source_urn"):
        SourceRecord.from_dict({"source_id": str(sid)})

    with pytest.raises(ModelFormatError, match="SourceRecord audit must be an AuditStamp"):
        SourceRecord.from_dict(
            {
                "source_id": str(sid),
                "source_urn": str(sample_source_urn),
                "record_category": "CENSUS",
                "description": "Valid",
                "repository_id": "REP-000001",
                "audit": "invalid",
            }
        )

    with pytest.raises(ModelFormatError, match="Failed to parse SourceRecord JSON string"):
        SourceRecord.from_json("{broken-json")


# ==============================================================================
# GROUP 4: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_source_models_immutability_and_introspection(
    golden_guid: str,
    golden_audit: AuditStamp,
    sample_source_urn: SourceURN,
) -> None:
    """Verify SourceReference, RecordMetadata, and SourceRecord frozen immutability and .help()."""
    ref = SourceReference.create("Bible")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        ref.citation_text = "New"  # type: ignore[misc]

    meta = RecordMetadata.create(golden_guid, "urn:x", "CAT", "TYPE")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        meta.record_type = "OTHER"  # type: ignore[misc]

    rec = SourceRecord.create(
        golden_guid,
        sample_source_urn,
        SourceRecordCategory.CENSUS,
        "Desc",
        "REP-000001",
        golden_audit,
    )
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        rec.description = "New Desc"  # type: ignore[misc]

    assert "update_citation" in (ref.help(as_str=True) or "")
    assert "create" in (meta.help(as_str=True) or "")
    assert "media_count" in (rec.help(as_str=True) or "")
