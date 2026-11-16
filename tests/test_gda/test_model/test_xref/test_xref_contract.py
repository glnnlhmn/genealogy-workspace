"""Path: tests/test_gda/test_model/test_xref/test_xref_contract.py

Authoritative public interface and contract verification suite for gda.model.xref.

Operational Role:
    Freezes and validates the 9-submodule topology, 12-symbol __all__ facade,
    submodule __all__ exports, IntrospectableMixin inheritance, frozen/strict
    Pydantic dataclass configuration, mandatory serialization and index key
    contracts (create, to_dict, from_dict, to_json, from_json, xref_key,
    sort_key, __lt__), and zero upward dependency leaks.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import pkgutil
from pathlib import Path

import pytest
from pydantic import ValidationError

import gda.model.xref as xref_pkg
import gda.model.xref.fact_participant_xref as fp_mod
import gda.model.xref.individual_family_xref as if_mod
import gda.model.xref.individual_organization_xref as io_mod
import gda.model.xref.individual_source_xref as isrc_mod
import gda.model.xref.individual_surname_xref as isur_mod
import gda.model.xref.location_xref as loc_mod
import gda.model.xref.media_xref as med_mod
import gda.model.xref.site_xref as site_mod
import gda.model.xref.surname_xref as sur_mod
from gda.core.introspectable import IntrospectableMixin
from gda.model.xref import (
    FactParticipantXRef,
    IndividualFamilyXRef,
    IndividualOrganizationXRef,
    IndividualSourceXRef,
    IndividualSurnameXRef,
    LocationXRef,
    MediaXRef,
    SiteXRef,
    SurnameXRef,
)

__version__ = "1.0.0+build.1"

_EXPECTED_SUBMODULES = {
    "fact_participant_xref",
    "individual_family_xref",
    "individual_organization_xref",
    "individual_source_xref",
    "individual_surname_xref",
    "location_xref",
    "media_xref",
    "site_xref",
    "surname_xref",
}

AUTHORITATIVE_XREF_EXPORTS = [
    "FactParticipantXRef",
    "IndividualFamilyXRef",
    "IndividualOrganizationXRef",
    "IndividualSourceXRef",
    "IndividualSurnameXRef",
    "LocationTargetID",
    "LocationXRef",
    "MediaTargetID",
    "MediaXRef",
    "SiteTargetID",
    "SiteXRef",
    "SurnameXRef",
]

_XREF_CLASSES = (
    FactParticipantXRef,
    IndividualFamilyXRef,
    IndividualOrganizationXRef,
    IndividualSourceXRef,
    IndividualSurnameXRef,
    LocationXRef,
    MediaXRef,
    SiteXRef,
    SurnameXRef,
)

_REQUIRED_XREF_MEMBERS = (
    "create",
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
    "xref_key",
    "sort_key",
    "__lt__",
)

_FORBIDDEN_IMPORTS = (
    "gda.enums",
    "gda.manager",
    "gda.db",
    "gda.engine",
    "cli",
    "ancestry_desk",
)


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_xref_package_submodule_topology_and_facade_exports() -> None:
    """Verify exact 9-submodule set and sorted 12-symbol __all__ facade for gda.model.xref."""
    discovered = {m.name for m in pkgutil.iter_modules(xref_pkg.__path__)}
    assert discovered == _EXPECTED_SUBMODULES

    actual = list(xref_pkg.__all__)
    assert actual == AUTHORITATIVE_XREF_EXPORTS
    assert actual == sorted(actual)
    assert len(actual) == 12

    for symbol in AUTHORITATIVE_XREF_EXPORTS:
        assert hasattr(xref_pkg, symbol), f"Missing exported symbol in gda.model.xref: {symbol}"


@pytest.mark.unit
@pytest.mark.integrity
def test_xref_submodule_exports_contract() -> None:
    """Verify exact sorted __all__ lists across all 9 gda.model.xref submodules."""
    assert fp_mod.__all__ == ["FactParticipantXRef"]
    assert if_mod.__all__ == ["IndividualFamilyXRef"]
    assert io_mod.__all__ == ["IndividualOrganizationXRef"]
    assert isrc_mod.__all__ == ["IndividualSourceXRef"]
    assert isur_mod.__all__ == ["IndividualSurnameXRef"]
    assert loc_mod.__all__ == ["LocationTargetID", "LocationXRef"]
    assert med_mod.__all__ == ["MediaTargetID", "MediaXRef"]
    assert site_mod.__all__ == ["SiteTargetID", "SiteXRef"]
    assert sur_mod.__all__ == ["SurnameXRef"]


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize("xref_cls", _XREF_CLASSES, ids=lambda c: c.__name__)
def test_xref_classes_enforce_frozen_strict_introspectable_and_members(
    xref_cls: type,
) -> None:
    """Verify every XRef class is a frozen strict Pydantic dataclass implementing IntrospectableMixin."""
    assert dataclasses.is_dataclass(xref_cls)
    assert issubclass(xref_cls, IntrospectableMixin)
    assert xref_cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]

    pydantic_cfg = getattr(xref_cls, "__pydantic_config__", {})
    assert pydantic_cfg.get("frozen") is True
    assert pydantic_cfg.get("extra") == "forbid"
    assert pydantic_cfg.get("strict") is True

    with pytest.raises(ValidationError):
        xref_cls(__unexpected_forbid_probe__="bad")  # type: ignore[call-arg]

    for member in _REQUIRED_XREF_MEMBERS:
        assert hasattr(xref_cls, member), f"{xref_cls.__name__} missing required member '{member}'"

    assert isinstance(xref_cls.xref_key, property)
    assert isinstance(xref_cls.sort_key, property)


@pytest.mark.unit
@pytest.mark.integrity
def test_xref_package_has_zero_upward_or_legacy_imports() -> None:
    """Verify gda.model.xref never imports legacy gda.enums or higher-level packages."""
    pkg_dir = Path(inspect.getfile(xref_pkg)).parent
    for py_path in pkg_dir.rglob("*.py"):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(_FORBIDDEN_IMPORTS), (
                        f"Forbidden import in {py_path}: '{alias.name}'"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith(_FORBIDDEN_IMPORTS), (
                    f"Forbidden import in {py_path}: '{node.module}'"
                )
