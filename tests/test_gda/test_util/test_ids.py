"""Path: tests/test_gda/test_util/test_ids.py

Unit verification suite for gda.util.ids.
"""

from __future__ import annotations

import pytest

import gda.util as util_pkg
import gda.util.ids as ids_mod
from gda.core.enums import IDType, SmartIDPrefix
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.util.ids import (
    extract_max_smart_id,
    mint_smart_id,
    mint_uuid,
    normalize_id,
    parse_smart_id,
    verify_id,
)

__version__ = "1.0.0+build.3"


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
    with pytest.raises(ValueError, match="cannot be negative"):
        mint_smart_id(SmartIDPrefix.LOC, -1)

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
    with pytest.raises(ValueError):
        extract_max_smart_id(["BAD"], ignore_errors=False)
