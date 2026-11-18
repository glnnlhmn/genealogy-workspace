"""Path: tests/test_gda/test_model/test_base/test_base_source.py

Unit, regression, and integration test suite verifying base source models.

Operational Role:
    Verifies SourceReference, RecordMetadata, and SourceRecord initialization,
    copy-on-write mutators, URN dispatch, subclass reflection, defensive
    validation boundaries, and JSON/dict serialization with 100% statement and
    branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.enums.core import AssociatedRole
from gda.core.enums.military import DraftCardTier
from gda.core.enums.sources import SourceRecordCategory
from gda.core.errors import ModelFormatError
from gda.model.atom.id import (
    DraftRecordID,
    IndividualID,
    LocationID,
    MediaID,
    RepositoryID,
    SourceID,
)
from gda.model.atom.scalar import ConfidenceScore, QuayScore
from gda.model.atom.urn import (
    ArchivalURN,
    CensusUrn,
    MilitaryDraftUrn,
    SourceURN,
    VitalCertificateUrn,
)
from gda.model.atom.year import HistoricalYear
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.source import (
    RecordMetadata,
    SourceRecord,
    SourceReference,
    _coerce_subclass_field,
    _resolve_archival_urn,
    _resolve_field_type,
    _serialize_subclass_field,
)
from gda.model.base.tombstone import Tombstone
from gda.model.source.military.draft import WwiDraftCardRecord, WwiPhysicalDescription

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: SOURCEREFERENCE LIFECYCLE & SERIALIZATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_source_reference_creation_and_mutators(golden_guid: str) -> None:
    """Verify SourceReference.create, mutators, and string representations."""
    sid = SourceID(golden_guid)
    sid_2 = SourceID("b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e")

    ref = SourceReference.create(
        citation_text="  1880 US Federal Census, Merrimack Co., NH  ",
        source_id=golden_guid,
        page_or_side="  ED 12, Sheet 4B  ",
        quay=2,
        confidence=0.85,
    )
    assert ref.citation_text == "1880 US Federal Census, Merrimack Co., NH"
    assert ref.source_id == sid
    assert ref.page_or_side == "ED 12, Sheet 4B"
    assert ref.quay == QuayScore(2)
    assert ref.confidence == ConfidenceScore(0.85)
    assert str(ref) == "1880 US Federal Census, Merrimack Co., NH (p. ED 12, Sheet 4B)"
    assert "SourceReference(" in repr(ref)

    assert ref.update_citation("1880 US Federal Census, Merrimack Co., NH") is ref
    up_cite = ref.update_citation("Revised Citation")
    assert up_cite.citation_text == "Revised Citation"

    assert ref.update_source_id(sid) is ref
    up_sid = ref.update_source_id(sid_2.value)
    assert up_sid.source_id == sid_2
    assert up_sid.update_source_id(None).source_id is None

    assert ref.update_page_or_side("ED 12, Sheet 4B") is ref
    up_page = ref.update_page_or_side("Sheet 5A")
    assert up_page.page_or_side == "Sheet 5A"
    no_page = up_page.update_page_or_side(None)
    assert no_page.page_or_side is None
    assert str(no_page) == "1880 US Federal Census, Merrimack Co., NH"

    assert ref.update_quay(QuayScore(2)) is ref
    up_quay = ref.update_quay(3)
    assert up_quay.quay == QuayScore(3)
    assert up_quay.update_quay(None).quay is None

    assert ref.update_confidence(ConfidenceScore(0.85)) is ref
    up_conf = ref.update_confidence(0.95)
    assert up_conf.confidence == ConfidenceScore(0.95)
    assert up_conf.update_confidence(None).confidence is None


@pytest.mark.unit
@pytest.mark.regression
def test_source_reference_validation_and_roundtrip(golden_guid: str) -> None:
    """Verify SourceReference boundary validations and dict/JSON round-trip."""
    full_ref = SourceReference.create(
        citation_text="Town Vital Register",
        source_id=SourceID(golden_guid),
        page_or_side="p. 42",
        quay=QuayScore(3),
        confidence=ConfidenceScore(0.99),
    )
    assert SourceReference.from_dict(full_ref.to_dict()) == full_ref
    assert SourceReference.from_json(full_ref.to_json()) == full_ref

    min_ref = SourceReference.create("Minimal Citation")
    assert min_ref.to_dict() == {"citation_text": "Minimal Citation"}
    assert SourceReference.from_dict(min_ref.to_dict()) == min_ref

    with pytest.raises(ModelFormatError, match="citation_text cannot be empty"):
        SourceReference(citation_text="   ")

    with pytest.raises(ModelFormatError, match="page_or_side cannot be blank"):
        SourceReference(citation_text="Valid", page_or_side="   ")

    with pytest.raises(ModelFormatError, match="citation_text cannot be empty"):
        SourceReference.create("   ")

    with pytest.raises(ModelFormatError, match="citation_text cannot be empty"):
        min_ref.update_citation("   ")

    with pytest.raises(ModelFormatError, match="payload must be a dictionary"):
        SourceReference.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'citation_text'"):
        SourceReference.from_dict({})

    with pytest.raises(ModelFormatError, match="Failed to parse SourceReference JSON"):
        SourceReference.from_json("{bad")


# ==============================================================================
# GROUP 2: RECORDMETADATA LIFECYCLE & SERIALIZATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_record_metadata_creation_and_roundtrip(golden_guid: str) -> None:
    """Verify RecordMetadata creation, optional repository_id, and serialization."""
    meta = RecordMetadata.create(
        source_id=golden_guid,
        source_urn="  URN:SRC:1880:NH_MERRIMACK:DOC_001  ",
        record_category="  CENSUS  ",
        record_type="  US_FEDERAL_POPULATION  ",
        repository_id="REP-000001",
    )
    assert meta.source_id == SourceID(golden_guid)
    assert meta.repository_id == RepositoryID("REP-000001")
    assert "RecordMetadata [CENSUS/US_FEDERAL_POPULATION]" in str(meta)
    assert "RecordMetadata(" in repr(meta)
    assert RecordMetadata.from_dict(meta.to_dict()) == meta
    assert RecordMetadata.from_json(meta.to_json()) == meta

    min_meta = RecordMetadata.create(
        source_id=SourceID(golden_guid),
        source_urn="URN:SRC:1880:NH_MERRIMACK:DOC_001",
        record_category="CENSUS",
        record_type="US_FEDERAL_POPULATION",
    )
    assert "repository_id" not in min_meta.to_dict()
    assert RecordMetadata.from_dict(min_meta.to_dict()) == min_meta

    with pytest.raises(ModelFormatError, match="cannot be empty"):
        RecordMetadata.create(golden_guid, "   ", "CAT", "TYPE")

    with pytest.raises(ModelFormatError, match="payload must be a dictionary"):
        RecordMetadata.from_dict(123)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        RecordMetadata.from_dict({"source_id": golden_guid})

    with pytest.raises(ModelFormatError, match="Failed to parse RecordMetadata JSON"):
        RecordMetadata.from_json("{bad")


# ==============================================================================
# GROUP 3: SOURCERECORD BASE & SUBCLASS REFLECTION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_source_record_base_creation_and_roundtrip(
    golden_guid: str,
    golden_audit: AuditStamp,
    sample_source_urn: SourceURN,
) -> None:
    """Verify base SourceRecord creation, properties, and dict/JSON serialization."""
    mid = MediaID("f0000000-0000-4000-8000-000000000001")
    person = AssociatedIndividual.create(
        individual_id="IND-000001",
        role=AssociatedRole.INFORMANT,
    )
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=golden_audit.updated_at,
        superseded_by=SourceID("b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e"),
    )

    rec = SourceRecord.create(
        source_id=golden_guid,
        source_urn=sample_source_urn.value,
        record_category="census",
        description="  1880 Census Household Extract  ",
        repository_id="REP-000001",
        audit=golden_audit,
        media_ids=[mid, mid.value],
        associated_people=[person, person.to_dict()],
        tombstone=tomb,
    )
    assert rec.is_deprecated is True
    assert rec.media_count == 1
    assert rec.participant_count == 2
    assert "SourceRecord [CENSUS]" in str(rec)
    assert "SourceRecord(" in repr(rec)

    d = rec.to_dict()
    assert SourceRecord.from_dict(d) == rec
    assert SourceRecord.from_json(rec.to_json()) == rec

    d_with_audit_obj = dict(d)
    d_with_audit_obj["audit"] = golden_audit
    d_with_audit_obj["tombstone"] = tomb
    assert SourceRecord.from_dict(d_with_audit_obj) == rec

    auto_audit_rec = SourceRecord.create(
        source_id=SourceID(golden_guid),
        source_urn=sample_source_urn,
        record_category=SourceRecordCategory.CENSUS,
        description="Auto audit record",
        repository_id=RepositoryID("REP-000001"),
    )
    assert auto_audit_rec.is_deprecated is False
    d_no_audit = auto_audit_rec.to_dict()
    del d_no_audit["audit"]
    rehydrated_no_audit = SourceRecord.from_dict(d_no_audit)
    assert rehydrated_no_audit.source_id == SourceID(golden_guid)


@pytest.mark.unit
def test_source_record_subclass_reflection_and_urn_helpers(
    golden_guid: str,
    golden_audit: AuditStamp,
) -> None:
    """Verify SourceRecord subclass reflection serialization/deserialization and helper branches."""
    assert isinstance(
        _resolve_archival_urn("URN:CENSUS:1880:US_PA:ED1_SH1"),
        CensusUrn,
    )
    assert isinstance(
        _resolve_archival_urn("URN:VITAL:BIRTH:1900:US_PA:BIR_001"),
        VitalCertificateUrn,
    )
    assert isinstance(
        _resolve_archival_urn("URN:GENERIC:SEG1:SEG2"),
        ArchivalURN,
    )
    assert _serialize_subclass_field({1: "one"}) == {1: "one"}
    assert _resolve_field_type(WwiDraftCardRecord, "NonExistentSymbol") is None
    assert _coerce_subclass_field(WwiDraftCardRecord, "str", None) is None
    assert _coerce_subclass_field(WwiDraftCardRecord, "str", "plain") == "plain"
    assert _coerce_subclass_field(WwiDraftCardRecord, "UnknownType", "val") == "val"
    assert _coerce_subclass_field(WwiDraftCardRecord, "int", "not-an-int") == "not-an-int"
    assert (
        _coerce_subclass_field(
            WwiDraftCardRecord,
            "DraftCardTier",
            DraftCardTier.WWI_FIRST,
        )
        is DraftCardTier.WWI_FIRST
    )

    draft = WwiDraftCardRecord(
        source_id=SourceID(golden_guid),
        source_urn=MilitaryDraftUrn("URN:DRAFT:1917:US_PA:DRF_001"),
        record_category=SourceRecordCategory.MILITARY,
        description="WWI Draft Registration Card",
        repository_id=RepositoryID("REP-000001"),
        audit=golden_audit,
        media_ids=[MediaID("f0000000-0000-4000-8000-000000000001")],
        associated_people=[
            AssociatedIndividual.create(
                individual_id="IND-000002",
                role=AssociatedRole.NEXT_OF_KIN,
            )
        ],
        draft_record_id=DraftRecordID("DRF-000001"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="John Lehman",
        draft_year=HistoricalYear(1917),
        board_jurisdiction_raw="Cumberland County Board No. 1",
        card_tier=DraftCardTier.WWI_FIRST,
        board_location_id=LocationID("LOC-000001"),
        occupation_verbatim="Blacksmith",
        physical_description=WwiPhysicalDescription(
            height_description="Tall",
            build_description="Medium",
            eye_color="Blue",
            hair_color="Brown",
        ),
    )

    payload = draft.to_dict()
    assert payload["draft_record_id"] == "DRF-000001"
    assert payload["physical_description"]["eye_color"] == "Blue"

    rehydrated = SourceRecord.from_dict.__func__(WwiDraftCardRecord, payload)  # type: ignore[attr-defined]
    assert rehydrated == draft


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
    mid = MediaID("f0000000-0000-4000-8000-000000000001")

    with pytest.raises(ModelFormatError, match="description.*cannot be empty"):
        SourceRecord(
            source_id=sid,
            source_urn=sample_source_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="   ",
            repository_id=rep,
            audit=golden_audit,
        )

    with pytest.raises(ModelFormatError, match="Duplicate MediaID in SourceRecord"):
        SourceRecord(
            source_id=sid,
            source_urn=sample_source_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Valid description",
            repository_id=rep,
            audit=golden_audit,
            media_ids=[mid, mid],
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

    with pytest.raises(ModelFormatError, match="payload must be a dictionary"):
        SourceRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id, source_urn"):
        SourceRecord.from_dict({"source_id": golden_guid})

    with pytest.raises(ModelFormatError, match="SourceRecord audit must be an AuditStamp"):
        SourceRecord.from_dict(
            {
                "source_id": golden_guid,
                "source_urn": sample_source_urn.value,
                "record_category": "CENSUS",
                "description": "Valid",
                "repository_id": "REP-000001",
                "audit": "bad-audit",
            }
        )

    with pytest.raises(ModelFormatError, match="Failed to parse SourceRecord JSON"):
        SourceRecord.from_json("{bad")

    with pytest.raises(ValidationError):
        SourceRecord(
            source_id=golden_guid,  # type: ignore[arg-type]
            source_urn=sample_source_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Strict rejection",
            repository_id=rep,
            audit=golden_audit,
        )


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
        rec.description = "Mutated"  # type: ignore[misc]

    assert "SourceReference" in (ref.help(as_str=True) or "")
    assert "RecordMetadata" in (meta.help(as_str=True) or "")
    assert "SourceRecord" in (rec.help(as_str=True) or "")
