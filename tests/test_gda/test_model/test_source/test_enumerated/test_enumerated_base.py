"""Path: tests/test_gda/test_model/test_source/test_enumerated/test_enumerated_base.py

Atomized behavioral test suite for EnumeratedRollRecord domain entity.

Operational Role:
    Verifies base enumerated roll instantiation, jurisdiction and enumerator
    string hygiene, coercion helpers, and dict/JSON serialization round-trips.
"""

from __future__ import annotations

import pytest

from gda.core.enums.fiscal import CitizenshipStatus
from gda.core.enums.sources import SourceRecordCategory
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, RepositoryID, SourceID, TranscriptID
from gda.model.atom.urn import ArchivalURN, CensusUrn, SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.base.tombstone import Tombstone
from gda.model.source.enumerated.base import (
    EnumeratedRollRecord,
    coerce_field_value,
    serialize_primitive_value,
)

__version__ = "1.0.0+build.6"


@pytest.mark.unit
@pytest.mark.smoke
def test_enumerated_roll_smoke_valid_initialization_and_roundtrip(
    valid_source_id: SourceID,
    valid_census_urn: CensusUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify instantiation, string hygiene, and dict/JSON serialization round-trips."""
    loc_id = LocationID("LOC-000042")
    trn_id = TranscriptID("e1a646d3-9c61-4a70-8b14-c48c8b417c8f")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=IsoTimestamp("2026-02-01T00:00:00Z"),
        superseded_by=SourceID("d9a646d3-9c61-4a70-8b14-c48c8b417c8e"),
    )

    rec = EnumeratedRollRecord(
        source_id=valid_source_id,
        source_urn=valid_census_urn,
        record_category=SourceRecordCategory.CENSUS,
        description="1880 Merrimack County Census Roll",
        repository_id=valid_repo_id,
        audit=valid_audit,
        tombstone=tomb,
        enumeration_year=HistoricalYear(1880),
        jurisdiction_raw="  Concord, Merrimack County, New Hampshire  ",
        jurisdiction_id=loc_id,
        enumerator_or_assessor_raw="  John A. White  ",
        transcript_id=trn_id,
    )
    assert rec.jurisdiction_raw == "Concord, Merrimack County, New Hampshire"
    assert rec.jurisdiction_id == loc_id
    assert rec.enumerator_or_assessor_raw == "John A. White"
    assert rec.transcript_id == trn_id
    assert "1880" in str(rec)
    assert "EnumeratedRollRecord(" in repr(rec)

    payload = rec.to_dict()
    restored = EnumeratedRollRecord.from_dict(payload)
    assert restored == rec

    json_str = rec.to_json()
    restored_json = EnumeratedRollRecord.from_json(json_str)
    assert restored_json == rec

    # Direct already-coerced object pass-through in from_dict
    direct = EnumeratedRollRecord.from_dict(
        {
            "source_id": valid_source_id,
            "source_urn": SourceURN("URN:SRC:1880:NH_MERRIMACK:ROLL_01"),
            "record_category": SourceRecordCategory.CENSUS,
            "description": "Direct objects",
            "repository_id": valid_repo_id,
            "audit": valid_audit,
            "enumeration_year": HistoricalYear(1880),
            "jurisdiction_raw": "Concord, NH",
            "enumerator_or_assessor_raw": "John A. White",
        }
    )
    assert direct.enumeration_year == HistoricalYear(1880)

    # Generic ArchivalURN deserialization branch
    generic_urn_rec = EnumeratedRollRecord.from_dict(
        {
            "source_id": str(valid_source_id),
            "source_urn": "URN:CUSTOM:1880:NH:DOC1",
            "record_category": "CENSUS",
            "description": "Generic URN",
            "repository_id": str(valid_repo_id),
            "audit": {
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
            "enumeration_year": 1880,
            "jurisdiction_raw": "Concord, NH",
        }
    )
    assert isinstance(generic_urn_rec.source_urn, ArchivalURN)


@pytest.mark.unit
@pytest.mark.regression
def test_enumerated_roll_validation_and_coercion_helpers(
    valid_source_id: SourceID,
    valid_census_urn: CensusUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify serialization/coercion edge cases and error branches."""

    class _CustomScalar:
        def __str__(self) -> str:
            return "custom-scalar"

    assert serialize_primitive_value(None) is None
    assert serialize_primitive_value(_CustomScalar()) == "custom-scalar"
    assert serialize_primitive_value(set()) == "set()"
    assert serialize_primitive_value([1, CitizenshipStatus.NATIVE_BORN]) == [1, "Native Born"]
    assert coerce_field_value("SourceID", None) is None
    loc = LocationID("LOC-000042")
    assert coerce_field_value("LocationID", loc) is loc
    assert coerce_field_value("LocationID", "LOC-000042") == loc
    assert coerce_field_value("RepositoryID", "REP-000001") == RepositoryID("REP-000001")
    assert coerce_field_value("ArchivalURN", "URN:CENSUS:1880:NH:P1") == CensusUrn(
        "URN:CENSUS:1880:NH:P1"
    )
    assert coerce_field_value("ArchivalURN", "URN:SRC:1880:NH:P1") == SourceURN(
        "URN:SRC:1880:NH:P1"
    )
    assert coerce_field_value("ArchivalURN", "URN:OTHER:1880:NH:P1") == ArchivalURN(
        "URN:OTHER:1880:NH:P1"
    )

    with pytest.raises(ModelFormatError, match="jurisdiction_raw.*cannot be empty"):
        EnumeratedRollRecord(
            source_id=valid_source_id,
            source_urn=valid_census_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Blank jurisdiction",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="   ",
        )

    with pytest.raises(ModelFormatError, match="enumerator_or_assessor_raw.*cannot be empty"):
        EnumeratedRollRecord(
            source_id=valid_source_id,
            source_urn=valid_census_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Blank enumerator",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            enumerator_or_assessor_raw="   ",
        )

    with pytest.raises(ModelFormatError, match="payload must be a dictionary"):
        EnumeratedRollRecord.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        EnumeratedRollRecord.from_dict({})

    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        EnumeratedRollRecord.from_dict(
            {
                "source_id": str(valid_source_id),
                "source_urn": str(valid_census_urn),
                "record_category": "CENSUS",
                "description": "Bad audit",
                "repository_id": str(valid_repo_id),
                "audit": "invalid-audit",
            }
        )

    with pytest.raises(ModelFormatError, match="Failed to parse EnumeratedRollRecord JSON"):
        EnumeratedRollRecord.from_json("{bad-json")
