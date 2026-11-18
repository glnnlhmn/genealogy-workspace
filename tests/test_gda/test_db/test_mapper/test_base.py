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

from gda.core.enums.sources import SourceRecordCategory
from gda.db.exceptions import EntityMappingError
from gda.db.mapper import base as base_mod
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

__version__ = "1.0.0+build.3"


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
    assert _extract_year_from_text("1880-05-12") == 1880
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

    active_src = SourceRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000002"),
        source_urn=SourceURN("URN:SRC:1880:US_PA:DOC_002"),
        record_category=SourceRecordCategory.OTHER,
        description="Active Source",
        repository_id=RepositoryID("REP-000001"),
        audit=audit,
    )
    assert _base_source_columns(active_src)["deprecated_at"] is None

    with pytest.raises(EntityMappingError, match="Missing or invalid 'payload_json'"):
        _hydrate_from_payload({"payload_json": ""}, BirthRecord)

    with pytest.raises(EntityMappingError, match="Failed to hydrate BirthRecord"):
        _hydrate_from_payload({"payload_json": "{bad-json"}, BirthRecord)


@pytest.mark.unit
def test_name_thing_notes_and_tombstone_helpers() -> None:
    """Verify _serialize_name_thing, _deserialize_name_thing, _deserialize_notes, and _deserialize_tombstone."""
    variant = HistoricVariant.create(raw="Old Town", name="Old Town")
    nt = NameThing(
        raw="New Town",
        canonical="New Town",
        aliases=["Townie"],
        alt_spellings=["Newtowne"],
        historic=[variant],
        comment="Historic parish",
    )
    flat = _serialize_name_thing(nt)
    assert _deserialize_name_thing(flat) == nt

    empty_nt = _deserialize_name_thing({"raw_name": "Simple", "canonical_name": "Simple"})
    assert empty_nt.aliases == []
    assert empty_nt.alt_spellings == []
    assert empty_nt.historic == []

    assert _deserialize_notes(None) == []
    assert _deserialize_notes("") == []

    active_tomb = _deserialize_tombstone({"is_deprecated": 0}, LocationID)
    assert active_tomb.is_deprecated is False

    dep_tomb = _deserialize_tombstone(
        {
            "is_deprecated": 1,
            "deprecated_at": None,
            "updated_at": "2026-02-01T00:00:00Z",
            "superseded_by": "LOC-000099",
        },
        LocationID,
    )
    assert dep_tomb.is_deprecated is True
    assert dep_tomb.deprecated_at == IsoTimestamp("2026-02-01T00:00:00Z")
    assert dep_tomb.superseded_by == LocationID("LOC-000099")

    dep_no_ts = _deserialize_tombstone({"is_deprecated": 1}, LocationID)
    assert dep_no_ts.is_deprecated is True
    assert dep_no_ts.deprecated_at is None
    assert dep_no_ts.superseded_by is None
