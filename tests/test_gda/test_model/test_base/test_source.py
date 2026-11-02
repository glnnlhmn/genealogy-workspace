"""Path: tests/test_gda/test_model/test_base/test_source.py

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

from gda.core.errors import ModelFormatError
from gda.enums.core import AssociatedRole
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import RepositoryID, SourceID
from gda.model.atom.scalar import ConfidenceScore, QuayScore
from gda.model.atom.urn import SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.source import RecordMetadata, SourceRecord, SourceReference
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.6"


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Fixture providing a standard test audit stamp."""
    ts = IsoTimestamp("2026-10-18T12:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


@pytest.fixture
def sample_source_urn() -> SourceURN:
    """Fixture providing a valid synthetic SourceURN."""
    return SourceURN("URN:SRC:1880:NH_MERRIMACK:DOC_000101")


# ==============================================================================
# GROUP 1: SOURCEREFERENCE BEHAVIORS, FACTORY & MUTATORS
# ==============================================================================


@pytest.mark.regression
def test_source_reference_factory_and_defaults() -> None:
    """Verify SourceReference factory constructor, defaults, and string formatting."""
    ref = SourceReference.create(
        citation_text="1880 US Census, Merrimack County, NH",
        source_id="c9a646d3-9c61-4a70-8b14-c48c8b417c8d",
        page_or_side="Folio 12B",
        quay=3,
        confidence=0.95,
    )
    assert ref.citation_text == "1880 US Census, Merrimack County, NH"
    assert ref.source_id == SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")
    assert ref.page_or_side == "Folio 12B"
    assert ref.quay == QuayScore(3)
    assert ref.confidence == ConfidenceScore(0.95)
    assert str(ref) == "1880 US Census, Merrimack County, NH (p. Folio 12B)"
    assert "Folio 12B" in repr(ref)

    # Minimal reference without page_or_side
    minimal = SourceReference.create("Family Bible Records")
    assert str(minimal) == "Family Bible Records"
    assert minimal.source_id is None
    assert minimal.page_or_side is None


@pytest.mark.regression
def test_source_reference_copy_on_write_mutators() -> None:
    """Verify SourceReference copy-on-write mutators and idempotent no-op returns."""
    original = SourceReference.create("Original Citation", page_or_side="p. 10")

    # update_citation
    up_text = original.update_citation("Updated Citation")
    assert up_text is not original
    assert up_text.citation_text == "Updated Citation"
    assert up_text.update_citation("Updated Citation") is up_text

    # update_source_id
    sid = SourceID("00000000-0000-4000-8000-000000000001")
    up_sid = original.update_source_id(sid)
    assert up_sid is not original
    assert up_sid.source_id == sid
    assert up_sid.update_source_id(sid) is up_sid

    # update_page_or_side
    up_page = original.update_page_or_side("p. 20")
    assert up_page is not original
    assert up_page.page_or_side == "p. 20"
    assert up_page.update_page_or_side("p. 20") is up_page

    # update_quay
    up_quay = original.update_quay(2)
    assert up_quay is not original
    assert up_quay.quay == QuayScore(2)
    assert up_quay.update_quay(2) is up_quay

    # update_confidence
    up_conf = original.update_confidence(0.85)
    assert up_conf is not original
    assert up_conf.confidence == ConfidenceScore(0.85)
    assert up_conf.update_confidence(0.85) is up_conf


@pytest.mark.integration
def test_source_reference_serialization_round_trip() -> None:
    """Verify SourceReference dictionary and JSON serialization round trip."""
    ref = SourceReference.create(
        citation_text="Town Records, Vol. 1",
        source_id="c9a646d3-9c61-4a70-8b14-c48c8b417c8d",
        page_or_side="p. 45",
        quay=2,
        confidence=0.9,
    )
    data = ref.to_dict()
    assert data["citation_text"] == "Town Records, Vol. 1"
    assert data["source_id"] == "c9a646d3-9c61-4a70-8b14-c48c8b417c8d"
    assert data["page_or_side"] == "p. 45"
    assert data["quay"] == 2
    assert data["confidence"] == 0.9

    restored = SourceReference.from_dict(data)
    assert restored == ref

    json_str = ref.to_json()
    assert SourceReference.from_json(json_str) == ref


@pytest.mark.integration
def test_source_reference_to_dict_minimal_omits_optional_keys() -> None:
    """Verify SourceReference.to_dict omits optional fields when None."""
    minimal = SourceReference.create("Bible Record")
    data = minimal.to_dict()
    assert data == {"citation_text": "Bible Record"}
    assert "source_id" not in data
    assert "page_or_side" not in data
    assert "quay" not in data
    assert "confidence" not in data


@pytest.mark.regression
def test_source_reference_defensive_errors() -> None:
    """Verify SourceReference defensive validations and rejections."""
    with pytest.raises(ModelFormatError, match="citation_text cannot be empty"):
        SourceReference(citation_text="")

    with pytest.raises(ModelFormatError, match="citation_text cannot be empty"):
        SourceReference.create("   ")

    with pytest.raises(ModelFormatError, match="citation_text cannot be empty"):
        SourceReference.create("Valid").update_citation("   ")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        SourceReference.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(
        ModelFormatError, match="Missing required field 'citation_text'"
    ):
        SourceReference.from_dict({"source_id": "c9a646d3-9c61-4a70-8b14-c48c8b417c8d"})

    with pytest.raises(
        ModelFormatError, match="Failed to parse SourceReference JSON string"
    ):
        SourceReference.from_json("{broken-json")


# ==============================================================================
# GROUP 2: RECORDMETADATA BEHAVIORS & VALIDATION
# ==============================================================================


@pytest.mark.regression
def test_record_metadata_factory_and_defaults() -> None:
    """Verify RecordMetadata factory instantiation, properties, and serialization with repo (closing line 255)."""
    meta = RecordMetadata.create(
        source_id="c9a646d3-9c61-4a70-8b14-c48c8b417c8d",
        source_urn="urn:gda:doc:census:1880",
        record_category="CENSUS",
        record_type="POPULATION",
        repository_id="REP-000001",
    )
    assert meta.source_id == SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")
    assert meta.source_urn == "urn:gda:doc:census:1880"
    assert meta.record_category == "CENSUS"
    assert meta.record_type == "POPULATION"
    assert meta.repository_id == RepositoryID("REP-000001")
    assert "RecordMetadata" in repr(meta)

    # Verify to_dict serializes repository_id when present (closing line 255)
    data = meta.to_dict()
    assert data["repository_id"] == "REP-000001"
    restored = RecordMetadata.from_dict(data)
    assert restored.repository_id == RepositoryID("REP-000001")


@pytest.mark.integration
def test_record_metadata_serialization_round_trip() -> None:
    """Verify RecordMetadata serialization and deserialization without repository_id."""
    meta = RecordMetadata.create(
        source_id="c9a646d3-9c61-4a70-8b14-c48c8b417c8d",
        source_urn="urn:gda:doc:probate:1850",
        record_category="PROBATE",
        record_type="WILL",
    )
    data = meta.to_dict()
    assert "repository_id" not in data

    restored = RecordMetadata.from_dict(data)
    assert restored == meta

    json_str = meta.to_json()
    assert RecordMetadata.from_json(json_str) == meta


@pytest.mark.regression
def test_record_metadata_defensive_errors() -> None:
    """Verify RecordMetadata boundary validations and rejections."""
    sid = SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")

    with pytest.raises((ValidationError, TypeError)):
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

    with pytest.raises(
        ModelFormatError, match="Failed to parse RecordMetadata JSON string"
    ):
        RecordMetadata.from_json("{broken-json")


@pytest.mark.regression
def test_record_metadata_post_init_type_defensive() -> None:
    """Verify RecordMetadata.__post_init__ raises TypeError when source_id is bypassed (closing line 210)."""
    meta = RecordMetadata.create(
        source_id="c9a646d3-9c61-4a70-8b14-c48c8b417c8d",
        source_urn="urn:test",
        record_category="TEST",
        record_type="TEST",
    )
    object.__setattr__(meta, "source_id", "not-a-source-id")
    with pytest.raises(TypeError, match="must be SourceID"):
        meta.__post_init__()


# ==============================================================================
# GROUP 3: SOURCERECORD COMPOSITE TESTS
# ==============================================================================


@pytest.mark.regression
def test_source_record_factory_and_properties(
    valid_audit: AuditStamp, sample_source_urn: SourceURN
) -> None:
    """Verify SourceRecord instantiation, properties, and string representation."""
    assoc = AssociatedIndividual.create(
        individual_id="IND-000001",
        role=AssociatedRole.INFORMANT,
        comment="Primary informant",
    )
    record = SourceRecord.create(
        source_id="c9a646d3-9c61-4a70-8b14-c48c8b417c8d",
        source_urn=sample_source_urn,
        record_category=SourceRecordCategory.CENSUS,
        description="1880 Federal Population Schedule for Bow",
        repository_id="REP-000001",
        audit=valid_audit,
        media_ids=["f0000000-0000-4000-8000-000000000001"],
        associated_people=[assoc],
    )

    assert record.is_deprecated is False
    assert record.media_count == 1
    assert record.participant_count == 1
    assert "SourceRecord [CENSUS]" in str(record)


@pytest.mark.integration
def test_source_record_serialization_round_trip(
    valid_audit: AuditStamp, sample_source_urn: SourceURN
) -> None:
    """Verify SourceRecord dictionary and JSON serialization round trip."""
    record = SourceRecord.create(
        source_id="c9a646d3-9c61-4a70-8b14-c48c8b417c8d",
        source_urn=sample_source_urn,
        record_category=SourceRecordCategory.VITAL,
        description="Birth Certificate entry",
        repository_id="REP-000002",
        audit=valid_audit,
        tombstone=Tombstone(
            is_deprecated=True,
            deprecated_at=valid_audit.created_at,
            superseded_by="c9a646d3-9c61-4a70-8b14-c48c8b417c8e",
        ),
    )
    assert record.is_deprecated is True

    data = record.to_dict()
    assert data["record_category"] == "VITAL"
    assert data["tombstone"]["is_deprecated"] is True

    restored = SourceRecord.from_dict(data)
    assert restored.source_id == record.source_id
    assert restored.is_deprecated is True
    assert restored.description == record.description

    json_str = record.to_json()
    assert SourceRecord.from_json(json_str).source_id == record.source_id


@pytest.mark.integration
def test_source_record_to_dict_and_from_dict_without_tombstone(
    valid_audit: AuditStamp, sample_source_urn: SourceURN
) -> None:
    """Verify SourceRecord omits tombstone in to_dict and parses payload without tombstone (closing 438->449)."""
    record = SourceRecord.create(
        source_id="c9a646d3-9c61-4a70-8b14-c48c8b417c8d",
        source_urn=sample_source_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Draft Card",
        repository_id="REP-000001",
        audit=valid_audit,
    )
    data = record.to_dict()
    assert "tombstone" not in data
    assert record.is_deprecated is False

    # from_dict when tombstone is completely omitted
    restored = SourceRecord.from_dict(data)
    assert restored.tombstone is None
    assert restored.is_deprecated is False


@pytest.mark.regression
def test_source_record_defensive_errors(
    valid_audit: AuditStamp, sample_source_urn: SourceURN
) -> None:
    """Verify SourceRecord boundary validations and error branches."""
    sid = SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")
    rep = RepositoryID("REP-000001")

    with pytest.raises(ModelFormatError, match="description.*cannot be empty"):
        SourceRecord(
            source_id=sid,
            source_urn=sample_source_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="   ",
            repository_id=rep,
            audit=valid_audit,
        )

    with pytest.raises((ValidationError, ModelFormatError)):
        SourceRecord(
            source_id=sid,
            source_urn="not-an-archival-urn",  # type: ignore[arg-type]
            record_category=SourceRecordCategory.CENSUS,
            description="Valid",
            repository_id=rep,
            audit=valid_audit,
        )

    with pytest.raises((ValidationError, ModelFormatError)):
        SourceRecord(
            source_id=sid,
            source_urn=sample_source_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Valid",
            repository_id="not-a-rep-id",  # type: ignore[arg-type]
            audit=valid_audit,
        )

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        SourceRecord.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id, source_urn"):
        SourceRecord.from_dict({"source_id": str(sid)})

    with pytest.raises(
        ModelFormatError, match="Failed to parse SourceRecord JSON string"
    ):
        SourceRecord.from_json("{broken-json")


@pytest.mark.regression
def test_source_record_post_init_defensive(
    valid_audit: AuditStamp, sample_source_urn: SourceURN
) -> None:
    """Verify SourceRecord.__post_init__ defensive error raises (closing lines 323, 329)."""
    record = SourceRecord.create(
        source_id="c9a646d3-9c61-4a70-8b14-c48c8b417c8d",
        source_urn=sample_source_urn,
        record_category=SourceRecordCategory.CENSUS,
        description="Valid description",
        repository_id="REP-000001",
        audit=valid_audit,
    )

    # Line 323: source_urn not an ArchivalURN
    object.__setattr__(record, "source_urn", "not-an-archival-urn")
    with pytest.raises(ModelFormatError, match="must be an instance of ArchivalURN"):
        record.__post_init__()

    # Restore source_urn and test Line 329: repository_id not a RepositoryID
    object.__setattr__(record, "source_urn", sample_source_urn)
    object.__setattr__(record, "repository_id", "not-a-rep-id")
    with pytest.raises(ModelFormatError, match="must be an instance of RepositoryID"):
        record.__post_init__()


# ==============================================================================
# GROUP 4: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.regression
def test_source_models_immutability_and_introspection(
    valid_audit: AuditStamp, sample_source_urn: SourceURN
) -> None:
    """Verify SourceReference, RecordMetadata, and SourceRecord frozen immutability and .help()."""
    ref = SourceReference.create("Bible")
    with pytest.raises((FrozenInstanceError, TypeError)):
        ref.citation_text = "New"  # type: ignore[misc]

    meta = RecordMetadata.create(
        "c9a646d3-9c61-4a70-8b14-c48c8b417c8d", "urn:x", "CAT", "TYPE"
    )
    with pytest.raises((FrozenInstanceError, TypeError)):
        meta.record_type = "OTHER"  # type: ignore[misc]

    rec = SourceRecord.create(
        "c9a646d3-9c61-4a70-8b14-c48c8b417c8d",
        sample_source_urn,
        SourceRecordCategory.CENSUS,
        "Desc",
        "REP-000001",
        valid_audit,
    )
    with pytest.raises((FrozenInstanceError, TypeError)):
        rec.description = "New Desc"  # type: ignore[misc]

    assert "update_citation" in ref.help(as_str=True)
    assert "create" in meta.help(as_str=True)
    assert "media_count" in rec.help(as_str=True)
