"""Path: tests/test_gda/test_model/test_enumerated/test_enumerated_topology.py

Package topology and public export contract verification for gda.model.enumerated.

Operational Role:
    Verifies __all__ alphabetical ordering, public attribute availability,
    SourceRecord inheritance across all schedule/roll records, and
    IntrospectableMixin compliance across all row/value models.
"""

from __future__ import annotations

import pytest

import gda.model.enumerated as ge_model
from gda.core.introspectable import IntrospectableMixin
from gda.model.base.source import SourceRecord

__version__ = "1.0.0+build.2"


@pytest.mark.smoke
@pytest.mark.integrity
@pytest.mark.unit
def test_enumerated_package_exports_and_sorting() -> None:
    """Verify gda.model.enumerated.__all__ is sorted and all attributes resolve."""
    assert ge_model.__all__ == sorted(ge_model.__all__)
    assert len(ge_model.__all__) == 38
    for symbol_name in ge_model.__all__:
        assert hasattr(ge_model, symbol_name), f"Missing exported symbol: {symbol_name}"


@pytest.mark.integrity
@pytest.mark.unit
def test_enumerated_records_and_entries_inheritance() -> None:
    """Verify every schedule/roll extends SourceRecord and every entry/property extends IntrospectableMixin."""
    record_classes = [
        getattr(ge_model, name)
        for name in ge_model.__all__
        if name.endswith("Record") or name.startswith("PopulationSchedule")
    ]
    assert len(record_classes) == 19
    for cls in record_classes:
        assert issubclass(cls, SourceRecord), f"{cls.__name__} must extend SourceRecord"

    entry_classes = [
        getattr(ge_model, name) for name in ge_model.__all__ if name.endswith(("Entry", "Property"))
    ]
    assert len(entry_classes) == 17
    for cls in entry_classes:
        assert issubclass(cls, IntrospectableMixin), (
            f"{cls.__name__} must extend IntrospectableMixin"
        )
