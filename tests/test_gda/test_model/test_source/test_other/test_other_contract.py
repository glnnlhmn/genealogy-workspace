"""Path: tests/test_gda/test_model/test_source/test_other/test_other_contract.py

Authoritative public interface and contract verification suite for gda.model.source.other.

Operational Role:
    Freezes and validates the submodule topology, sorted __all__ facade,
    SourceRecord and IntrospectableMixin inheritance, centralized
    URN_REGEXES['OTHER'] usage, and serialization method contracts for
    OtherMiscellaneousRecord.
"""

from __future__ import annotations

import dataclasses
import pkgutil

import pytest

import gda.model.source.other as other_pkg
import gda.model.source.other.miscellaneous as misc_mod
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import URN_REGEXES
from gda.model.base.source import SourceRecord
from gda.model.source.other import OtherMiscellaneousRecord

__version__ = "1.0.0+build.1"

AUTHORITATIVE_OTHER_EXPORTS = [
    "OtherMiscellaneousRecord",
]


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_other_package_topology_and_exports_contract() -> None:
    """Verify gda.model.source.other submodule topology and sorted __all__ exports."""
    discovered = {m.name for m in pkgutil.iter_modules(other_pkg.__path__)}
    assert discovered == {"miscellaneous"}
    assert other_pkg.__all__ == AUTHORITATIVE_OTHER_EXPORTS
    assert other_pkg.__all__ == sorted(other_pkg.__all__)
    assert misc_mod.__all__ == ["OtherMiscellaneousRecord"]
    assert misc_mod._OTHER_URN_PATTERN is URN_REGEXES["OTHER"]


@pytest.mark.unit
@pytest.mark.integrity
def test_other_miscellaneous_record_inheritance_and_methods_contract() -> None:
    """Verify OtherMiscellaneousRecord extends SourceRecord and enforces frozen/strict invariants."""
    assert dataclasses.is_dataclass(OtherMiscellaneousRecord)
    assert issubclass(OtherMiscellaneousRecord, SourceRecord)
    assert issubclass(OtherMiscellaneousRecord, IntrospectableMixin)
    assert OtherMiscellaneousRecord.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    for method in ("create", "to_dict", "from_dict", "to_json", "from_json"):
        assert callable(getattr(OtherMiscellaneousRecord, method))
