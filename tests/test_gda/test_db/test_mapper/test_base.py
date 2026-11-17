"""Path: tests/test_gda/test_db/test_mapper/test_base.py

Unit verification suite for BaseRowMapper and shared serialization helpers.

Operational Role:
    1:1 verification suite for src/gda/db/mapper/base.py. Validates
    BaseRowMapper.model_cls, IntrospectableMixin help(), _extract_id_str,
    _extract_year_from_text, _opt_val, _opt_year, _opt_bool_int, _date_year,
    _date_sort, _base_source_columns, _hydrate_from_payload,
    _serialize_name_thing, _deserialize_name_thing, _deserialize_notes, and
    _deserialize_tombstone.
"""

from __future__ import annotations

import pytest

import gda.db.mapper.base as base_mod
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.base import (
    _base_source_columns,
    _date_sort,
    _date_year,
    _deserialize_name_thing,
    _deserialize_notes,
    _deserialize_tombstone,
    _extract_id_str,
    _extract_year_from_text,
    _hydrate_from_payload,
    _opt_bool_int,
    _opt_val,
    _opt_year,
    _serialize_name_thing,
)
from gda.db.mapper.places import LocationRowMapper
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone
from gda.model.source.vital.birth import BirthRecord

__version__ = "1.0.0+build.2"


@pytest.mark.unit
def test_mapper_base_dunder_all_and_model_cls_contract() -> None:
    """Verify gda.db.mapper.base.__all__ is sorted and BaseRowMapper exposes model_cls."""
    assert base_mod.__all__ == sorted(base_mod.__all__)
    mapper = LocationRowMapper()
    assert mapper.model_cls is not None

    help_doc = mapper.help(as_str=True)
    assert help_doc is not None
    assert "LocationRowMapper" in help_doc


@pytest.mark.unit
def test_extract_id_str_and_extract_year_from_text() -> None:
    """Verify all branches of _extract_id_str and _extract_year_from_text."""
    assert _extract_id_str(None) is None
    assert _extract_id_str("LOC-000001") == "LOC-000001"
    assert _extract_id_str({"value": "LOC-000002"}) == "LOC-000002"
    assert _extract_id_str(LocationID("LOC-000003")) == "LOC-000003"
    assert _extract_id_str(12345) == "12345"

    assert _extract_year_from_text(None) is None
    assert _extract_year_from_text("") is None
    assert _extract_year_from_text("Born in 1865 in NH") == 1865
    assert _extract_year_from_text("Circa 1905") == 1905
    assert _extract_year_from_text("Undated") is None


@pytest.mark.unit
def test_source_mapper_shared_helpers() -> None:
    """Verify _opt_val, _opt_year, _opt_bool_int, _date_year, _date_sort, _base_source_columns, and _hydrate_from_payload."""
    assert _opt_val(None) is None
    assert _opt_val("raw") == "raw"
    assert _opt_val(LocationID("LOC-000001")) == "LOC-000001"

    assert _opt_year(None) is None
    assert _opt_year(HistoricalYear(1900)) == 1900

    assert _opt_bool_int(None) is None
    assert _opt_bool_int(True) == 1
    assert _opt_bool_int(False) == 0

    assert _date_year(None) is None
    assert _date_year(EventDate.from_dict("1880-05-12")) == 1880

    assert _date_sort(None) is None
    assert _date_sort(EventDate.from_dict("1880")) == "1880"

    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    audit = AuditStamp(created_at=ts, updated_at=ts)
    src = SourceRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000001"),
        source_urn=SourceURN("URN:SRC:1880:US_PA:DOC_001"),
        record_category=SourceRecordCategory.OTHER,
        description="Base Source",
        repository_id=RepositoryID("REP-000001"),
        audit=audit,
        tombstone=Tombstone[SourceID](
            is_deprecated=True,
            deprecated_at=ts,
        ),
    )
    cols = _base_source_columns(src)
    assert cols["record_type"] == "OTHER"
    assert cols["deprecated_at"] == "2026-01-01T00:00:00Z"
    assert _hydrate_from_payload(cols, SourceRecord) == src

    birth = BirthRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000002"),
        source_urn=SourceURN("URN:SRC:1880:US_PA:BIR_002"),
        record_type=SourceRecordType.BIRTH_CERTIFICATE,
        description="Birth",
        repository_id=RepositoryID("REP-000001"),
        audit=audit,
        child_name_raw="John Lehman",
        date_of_birth=EventDate.from_dict("1880-05-12"),
        place_of_birth_raw="Carlisle",
    )
    b_cols = _base_source_columns(birth)
    assert b_cols["record_type"] == "BIRTH_CERTIFICATE"
    assert _hydrate_from_payload(b_cols, BirthRecord) == birth

    with pytest.raises(EntityMappingError, match="Missing or invalid 'payload_json'"):
        _hydrate_from_payload({"payload_json": None}, BirthRecord)
    with pytest.raises(EntityMappingError, match="Failed to hydrate"):
        _hydrate_from_payload({"payload_json": "{bad-json"}, BirthRecord)


@pytest.mark.unit
def test_name_thing_notes_and_tombstone_helpers() -> None:
    """Verify _serialize_name_thing, _deserialize_name_thing, _deserialize_notes, and _deserialize_tombstone."""
    name = NameThing.create(
        raw="Bow",
        canonical="Bow",
        aliases=["Bow Mills"],
        alt_spellings=["Bowe"],
        historic=[HistoricVariant.create(raw="Bow Town", name="Bow Town")],
        comment="Historic town",
    )
    cols = _serialize_name_thing(name)
    assert _deserialize_name_thing(cols) == name

    assert _deserialize_notes(None) == []
    assert _deserialize_notes("") == []

    active_ts = _deserialize_tombstone({"is_deprecated": 0}, LocationID)
    assert active_ts.is_deprecated is False

    dep_fallback = _deserialize_tombstone(
        {
            "is_deprecated": 1,
            "deprecated_at": None,
            "updated_at": "2026-01-01T00:00:00Z",
            "superseded_by": "LOC-000009",
        },
        LocationID,
    )
    assert dep_fallback.is_deprecated is True
    assert dep_fallback.superseded_by == LocationID("LOC-000009")
