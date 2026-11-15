"""Path: tests/test_gda/test_model/test_source/test_land/test_land_contract.py

Authoritative public interface and contract verification suite for gda.model.source.land.

Operational Role:
    Freezes and validates the 2-submodule topology (deed, grant), sorted
    __all__ facade, SourceRecord and IntrospectableMixin inheritance,
    centralized URN_REGEXES['LAND'] integration, and serialization method
    contracts for DeedParty, LandDeedRecord, LandGrantRecord, and LandParcel.
"""

from __future__ import annotations

import dataclasses
import pkgutil

import pytest

import gda.model.source.land as land_pkg
import gda.model.source.land.deed as deed_mod
import gda.model.source.land.grant as grant_mod
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import URN_REGEXES
from gda.model.base.source import SourceRecord
from gda.model.source.land import (
    DeedParty,
    LandDeedRecord,
    LandGrantRecord,
    LandParcel,
)

__version__ = "1.0.0+build.1"

AUTHORITATIVE_LAND_EXPORTS = [
    "DeedParty",
    "LandDeedRecord",
    "LandGrantRecord",
    "LandParcel",
]


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_land_package_topology_and_exports_contract() -> None:
    """Verify gda.model.source.land submodule topology and sorted __all__ exports."""
    discovered = {m.name for m in pkgutil.iter_modules(land_pkg.__path__)}
    assert discovered == {"deed", "grant"}
    assert land_pkg.__all__ == AUTHORITATIVE_LAND_EXPORTS
    assert land_pkg.__all__ == sorted(land_pkg.__all__)
    assert deed_mod.__all__ == ["DeedParty", "LandDeedRecord", "LandParcel"]
    assert grant_mod.__all__ == ["LandGrantRecord"]
    assert deed_mod._LAND_URN_PATTERN is URN_REGEXES["LAND"]
    assert grant_mod._LAND_URN_PATTERN is URN_REGEXES["LAND"]


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize(
    "cls",
    (DeedParty, LandDeedRecord, LandGrantRecord, LandParcel),
    ids=lambda c: c.__name__,
)
def test_land_classes_enforce_frozen_strict_and_serialization(cls: type) -> None:
    """Verify all land dataclasses enforce frozen/strict config and serialization methods."""
    assert dataclasses.is_dataclass(cls)
    assert issubclass(cls, IntrospectableMixin)
    assert cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    if cls in (LandDeedRecord, LandGrantRecord):
        assert issubclass(cls, SourceRecord)
    for method in ("create", "to_dict", "from_dict", "to_json", "from_json"):
        assert callable(getattr(cls, method))
