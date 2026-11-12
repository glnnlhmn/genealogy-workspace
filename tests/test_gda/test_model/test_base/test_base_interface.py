"""Path: tests/test_gda/test_model/test_base/test_base_interface.py

Package-wide architectural and public interface contract lock for gda.model.base.

Operational Role:
    Locks down the exact submodule layout, unified __all__ facade exports,
    dataclass immutability/strictness configuration, and IntrospectableMixin
    compliance across all Batch 1, Batch 2, and Batch 3 models in gda.model.base.
"""

from __future__ import annotations

import dataclasses
import pkgutil

import pytest
from pydantic import ValidationError

import gda.model.base as base_pkg
from gda.core.introspectable import IntrospectableMixin

__version__ = "1.0.0+build.2"

_EXPECTED_SUBMODULES = {
    "address",
    "age",
    "association",
    "audit",
    "date",
    "entity",
    "envelope",
    "family",
    "geo",
    "media",
    "name",
    "note",
    "source",
    "tombstone",
    "transcript",
}

_EXPECTED_FACADE_ALL = [
    "Address",
    "Age",
    "AssociatedIndividual",
    "AuditStamp",
    "BaseEntity",
    "BaseEntityGUID",
    "CanonicalName",
    "ChildLink",
    "Coordinates",
    "DocumentSide",
    "EntityLifecycleMixin",
    "EventDate",
    "FamilyUnion",
    "HistoricVariant",
    "HistoricalName",
    "Legibility",
    "Media",
    "NameBase",
    "NameLifecycleMixin",
    "NamePerson",
    "NameThing",
    "Note",
    "RecordMetadata",
    "RegistryEnvelope",
    "SourceRecord",
    "SourceReference",
    "TextQuality",
    "TimePeriod",
    "Tombstone",
    "Transcript",
    "is_tombstoned",
    "stamp_tombstone",
]


@pytest.mark.unit
@pytest.mark.regression
def test_base_package_submodule_topology_and_facade_exports() -> None:
    """Verify exact submodule set and __all__ facade exports for gda.model.base."""
    discovered = {m.name for m in pkgutil.iter_modules(base_pkg.__path__)}
    assert discovered == _EXPECTED_SUBMODULES
    assert base_pkg.__all__ == _EXPECTED_FACADE_ALL

    for symbol in _EXPECTED_FACADE_ALL:
        assert hasattr(base_pkg, symbol), f"Missing exported symbol: {symbol}"


@pytest.mark.unit
@pytest.mark.regression
def test_all_base_dataclasses_enforce_frozen_extra_forbid_and_introspection() -> None:
    """Verify every dataclass exported by gda.model.base enforces frozen, extra='forbid', and IntrospectableMixin."""
    dataclass_types = [
        getattr(base_pkg, name)
        for name in _EXPECTED_FACADE_ALL
        if isinstance(getattr(base_pkg, name), type)
        and dataclasses.is_dataclass(getattr(base_pkg, name))
    ]
    assert len(dataclass_types) == 25

    for cls in dataclass_types:
        assert issubclass(cls, IntrospectableMixin), (
            f"{cls.__name__} must inherit IntrospectableMixin"
        )
        params = cls.__dataclass_params__
        assert params.frozen is True, f"{cls.__name__} must be frozen=True"

        with pytest.raises(ValidationError):
            cls(__unexpected_forbid_probe__="bad")  # type: ignore[call-arg]
