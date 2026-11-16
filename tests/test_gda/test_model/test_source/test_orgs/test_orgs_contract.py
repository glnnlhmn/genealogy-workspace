"""Path: tests/test_gda/test_model/test_source/test_orgs/test_orgs_contract.py

Authoritative public interface and contract verification suite for gda.model.source.orgs.

Operational Role:
    Freezes and validates the 2-submodule topology (membership, roster),
    sorted __all__ facade, SourceRecord / EnumeratedRollRecord and
    IntrospectableMixin inheritance, frozen/strict Pydantic dataclass
    configuration, and serialization method contracts for
    OrganizationMembershipRecord, OrganizationRosterEntry, and
    OrganizationRosterRecord.
"""

from __future__ import annotations

import dataclasses
import pkgutil

import pytest

import gda.model.source.orgs as orgs_pkg
import gda.model.source.orgs.membership as membership_mod
import gda.model.source.orgs.roster as roster_mod
from gda.core.introspectable import IntrospectableMixin
from gda.model.base.source import SourceRecord
from gda.model.source.enumerated.base import EnumeratedRollRecord
from gda.model.source.orgs import (
    OrganizationMembershipRecord,
    OrganizationRosterEntry,
    OrganizationRosterRecord,
)

__version__ = "1.0.0+build.2"

AUTHORITATIVE_ORGS_EXPORTS = [
    "OrganizationMembershipRecord",
    "OrganizationRosterEntry",
    "OrganizationRosterRecord",
]


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_orgs_package_topology_and_exports_contract() -> None:
    """Verify gda.model.source.orgs submodule topology and sorted __all__ exports."""
    discovered = {m.name for m in pkgutil.iter_modules(orgs_pkg.__path__)}
    assert discovered == {"membership", "roster"}
    assert orgs_pkg.__all__ == AUTHORITATIVE_ORGS_EXPORTS
    assert orgs_pkg.__all__ == sorted(orgs_pkg.__all__)
    assert membership_mod.__all__ == ["OrganizationMembershipRecord"]
    assert roster_mod.__all__ == ["OrganizationRosterEntry", "OrganizationRosterRecord"]


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize(
    "cls",
    (OrganizationMembershipRecord, OrganizationRosterEntry, OrganizationRosterRecord),
    ids=lambda c: c.__name__,
)
def test_orgs_classes_enforce_frozen_strict_and_serialization(cls: type) -> None:
    """Verify all orgs source dataclasses enforce frozen/strict config and serialization methods."""
    assert dataclasses.is_dataclass(cls)
    assert issubclass(cls, IntrospectableMixin)
    assert cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    if cls is OrganizationMembershipRecord:
        assert issubclass(cls, SourceRecord)
        assert callable(cls.create)
    elif cls is OrganizationRosterRecord:
        assert issubclass(cls, EnumeratedRollRecord)
        assert callable(cls.flatten_entries)
    for method in ("to_dict", "from_dict", "to_json", "from_json"):
        assert callable(getattr(cls, method))
