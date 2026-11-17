"""Path: tests/test_gda/test_util/test_ids.py

Unit verification suite for gda.util.ids.

Operational Role:
    Verifies identifier normalization, SmartID and UUIDv4 verification, minting,
    parsing, high-water mark sequence extraction, polymorphic ID resolution, and
    primitive unwrapping helpers with 100% statement and branch coverage.
"""

from __future__ import annotations

import pytest

import gda.util as util_pkg
import gda.util.ids as ids_mod
from gda.core.enums import CensusYearUS, IDType, SmartIDPrefix
from gda.core.errors import ModelFormatError
from gda.model.atom.id import IndividualID, LocationID, SiteID, SourceID
from gda.util.ids import (
    extract_max_smart_id,
    mint_smart_id,
    mint_uuid,
    normalize_id,
    parse_smart_id,
    resolve_polymorphic_id,
    unwrap_bool_int,
    unwrap_int,
    unwrap_value,
    verify_id,
)

__version__ = "1.0.0+build.4"


@pytest.mark.unit
def test_ids_exports_and_normalize_id() -> None:
    """Verify gda.util.ids.__all__ is sorted and normalize_id unwraps atoms, dicts, strings, and errors."""
    assert ids_mod.__all__ == sorted(ids_mod.__all__)
    assert util_pkg.__all__ == sorted(util_pkg.__all__)
    assert normalize_id("IND-000001") == "IND-000001"
    assert normalize_id({"value": "LOC-000001"}) == "LOC-000001"
    assert normalize_id(IndividualID("IND-000001")) == "IND-000001"
    assert normalize_id(LocationID("LOC-000002")) == "LOC-000002"
    assert (
        normalize_id(SourceID("00000000-0000-4000-8000-000000000001"))
        == "00000000-0000-4000-8000-000000000001"
    )
    assert normalize_id(42) == "42"

    with pytest.raises(ValueError, match="Cannot normalize identifier from None"):
        normalize_id(None)

    with pytest.raises(ValueError, match="cannot be empty or whitespace"):
        normalize_id("   ")


@pytest.mark.unit
def test_unwrap_value_int_and_bool_int_helpers() -> None:
    """Verify unwrap_value, unwrap_int, and unwrap_bool_int across atoms, enums, and primitives."""
    assert unwrap_value(None) is None
    assert unwrap_value("plain") == "plain"
    assert unwrap_value(LocationID("LOC-000001")) == "LOC-000001"
    assert unwrap_value(SmartIDPrefix.LOC) == "LOC"

    assert unwrap_int(None) is None
    assert unwrap_int(1880) == 1880
    assert unwrap_int("1900") == 1900
    assert unwrap_int(CensusYearUS.Y1880) == 1880

    with pytest.raises(ValueError, match="Boolean value"):
        unwrap_int(True)

    class _BoolAtom:
        value = False

    with pytest.raises(ValueError, match="Boolean value"):
        unwrap_int(_BoolAtom())

    assert unwrap_bool_int(None) is None
    assert unwrap_bool_int(True) == 1
    assert unwrap_bool_int(False) == 0
    assert unwrap_bool_int(1) == 1
    assert unwrap_bool_int(0) == 0


@pytest.mark.unit
def test_verify_id_smart_id_and_uuid_branches() -> None:
    """Verify verify_id across SmartID, UUIDv4, invalid prefixes, and error branches."""
    with pytest.raises(TypeError, match="must be a string"):
        verify_id(123)  # type: ignore[arg-type]

    assert verify_id("   ") is False
    assert verify_id("IND-000001") is True
    assert (
        verify_id(
            "IND-000001",
            id_type=IDType.SMART_ID,
            smart_id_prefix=SmartIDPrefix.IND,
        )
        is True
    )
    assert (
        verify_id(
            "IND-000001",
            id_type=IDType.SMART_ID,
            smart_id_prefix=SmartIDPrefix.LOC,
        )
        is False
    )
    assert verify_id("BAD-000001", id_type=IDType.SMART_ID) is False
    assert verify_id("not-an-id", id_type=IDType.SMART_ID) is False
    assert verify_id("IND-000001", id_type="UNSUPPORTED") is False  # type: ignore[arg-type]

    u = mint_uuid()
    assert verify_id(u, id_type=IDType.UUID) is True
    with pytest.raises(ValueError, match="smart_id_prefix cannot be specified"):
        verify_id(u, id_type=IDType.UUID, smart_id_prefix=SmartIDPrefix.IND)


@pytest.mark.unit
def test_mint_parse_and_extract_max_smart_id() -> None:
    """Verify mint_smart_id, parse_smart_id, and extract_max_smart_id."""
    assert mint_smart_id(SmartIDPrefix.LOC, 42) == "LOC-000042"
    assert mint_smart_id("LOC", 42) == "LOC-000042"
    with pytest.raises(ValueError, match="cannot be negative"):
        mint_smart_id(SmartIDPrefix.LOC, -1)
    with pytest.raises(ValueError, match="Padding width must be at least 1"):
        mint_smart_id(SmartIDPrefix.LOC, 1, padding=0)

    assert parse_smart_id("LOC-000042") == (SmartIDPrefix.LOC, 42)
    assert parse_smart_id(LocationID("LOC-000042")) == (SmartIDPrefix.LOC, 42)
    with pytest.raises(ValueError, match="Cannot parse smartID"):
        parse_smart_id("")
    with pytest.raises(ValueError, match="does not conform"):
        parse_smart_id("INVALID")

    assert extract_max_smart_id(None) == 0
    assert extract_max_smart_id("LOC-000001") == 0
    items = ["LOC-000005", LocationID("LOC-000012"), "IND-000099", "BAD"]
    assert extract_max_smart_id(items, prefix=SmartIDPrefix.LOC) == 12
    assert extract_max_smart_id(items, prefix="LOC") == 12
    with pytest.raises(ValueError):
        extract_max_smart_id(["BAD"], ignore_errors=False)


@pytest.mark.unit
def test_resolve_polymorphic_id_dispatches_smart_ids_and_uuids() -> None:
    """Verify resolve_polymorphic_id resolves existing instances, SmartIDs, and UUIDs."""
    prefix_map = {
        SmartIDPrefix.IND: IndividualID,
        SmartIDPrefix.LOC: LocationID,
    }
    ind = IndividualID("IND-000001")
    src = SourceID("00000000-0000-4000-8000-000000000001")

    assert resolve_polymorphic_id(ind, prefix_map=prefix_map, uuid_cls=SourceID) is ind
    assert resolve_polymorphic_id(src, prefix_map=prefix_map, uuid_cls=SourceID) is src
    assert resolve_polymorphic_id(
        "LOC-000005", prefix_map=prefix_map, uuid_cls=SourceID
    ) == LocationID("LOC-000005")
    assert (
        resolve_polymorphic_id(
            "00000000-0000-4000-8000-000000000001",
            prefix_map=prefix_map,
            uuid_cls=SourceID,
        )
        == src
    )

    with pytest.raises(ModelFormatError, match="non-empty identifier"):
        resolve_polymorphic_id("   ", prefix_map=prefix_map)

    with pytest.raises(ModelFormatError, match="non-empty identifier"):
        resolve_polymorphic_id(None, prefix_map=prefix_map)

    # Valid SmartID prefix (SID), but not in allowed prefix_map
    with pytest.raises(ModelFormatError, match="does not match any supported"):
        resolve_polymorphic_id("SID-000001", prefix_map=prefix_map, uuid_cls=SourceID)

    # Wrong AtomID instance not in prefix_map
    with pytest.raises(ModelFormatError, match="non-empty identifier"):
        resolve_polymorphic_id(SiteID("SID-000001"), prefix_map=prefix_map)
