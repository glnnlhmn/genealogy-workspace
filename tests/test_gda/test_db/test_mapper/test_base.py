"""Path: tests/test_gda/test_db/test_mapper/test_base.py

Unit verification suite for BaseRowMapper and shared serialization helpers.

Operational Role:
    1:1 verification suite for src/gda/db/mapper/base.py. Validates
    BaseRowMapper.model_cls, IntrospectableMixin help(), _extract_id_str,
    _extract_year_from_text, _serialize_name_thing, _deserialize_name_thing,
    _deserialize_notes, and _deserialize_tombstone.
"""

from __future__ import annotations

import pytest

import gda.db.mapper.base as base_mod
from gda.db.mapper.base import (
    _deserialize_name_thing,
    _deserialize_notes,
    _deserialize_tombstone,
    _extract_id_str,
    _extract_year_from_text,
    _serialize_name_thing,
)
from gda.db.mapper.places import LocationRowMapper
from gda.model.atom.id import LocationID
from gda.model.base.name import HistoricVariant, NameThing

__version__ = "1.0.0+build.1"


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
