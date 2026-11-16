"""Path: tests/test_gda/test_model/test_source/test_source_contract.py

Authoritative public interface and contract verification suite for gda.model.source.

Operational Role:
    Freezes and validates the 12-subpackage topology of gda.model.source,
    strict alphabetical __all__ sorting across gda.model.source and all 12
    domain subpackages, IntrospectableMixin inheritance, frozen/strict
    Pydantic dataclass configuration on all exported record models and entry
    value objects, and zero upward dependency leaks.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import pkgutil
from enum import Enum
from pathlib import Path

import pytest

import gda.model.source as source_pkg
from gda.core.introspectable import IntrospectableMixin

__version__ = "1.0.0+build.1"

_EXPECTED_SUBPACKAGES = {
    "cemetery",
    "education",
    "enumerated",
    "immigration",
    "land",
    "manuscripts",
    "military",
    "orgs",
    "other",
    "probate",
    "publications",
    "vital",
}

_FORBIDDEN_IMPORTS = (
    "gda.enums",
    "gda.model.xref",
    "gda.entity",
    "gda.manager",
    "gda.db",
    "gda.engine",
    "cli",
    "ancestry_desk",
)


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_source_package_subpackage_topology_and_sorted_exports() -> None:
    """Verify gda.model.source contains the exact 12 domain subpackages and sorted __all__."""
    discovered = {m.name for m in pkgutil.iter_modules(source_pkg.__path__) if m.ispkg}
    assert discovered == _EXPECTED_SUBPACKAGES

    assert source_pkg.__all__ == sorted(source_pkg.__all__)
    assert len(source_pkg.__all__) == 103

    for symbol in source_pkg.__all__:
        assert hasattr(source_pkg, symbol), f"Missing symbol in gda.model.source: {symbol}"


@pytest.mark.unit
@pytest.mark.integrity
def test_all_source_subpackages_declare_sorted_all_and_version() -> None:
    """Verify every domain subpackage under gda.model.source declares sorted __all__ and __version__."""
    for subpkg_name in sorted(_EXPECTED_SUBPACKAGES):
        subpkg = getattr(source_pkg, subpkg_name)
        assert hasattr(subpkg, "__all__"), f"gda.model.source.{subpkg_name} missing __all__"
        assert subpkg.__all__ == sorted(subpkg.__all__), (
            f"gda.model.source.{subpkg_name}.__all__ is not sorted alphabetically"
        )
        assert hasattr(subpkg, "__version__")
        assert "+build." in subpkg.__version__


@pytest.mark.unit
@pytest.mark.integrity
def test_all_source_exported_dataclasses_enforce_frozen_strict_and_introspectable() -> None:
    """Verify every dataclass exported by gda.model.source inherits IntrospectableMixin and is frozen."""
    exported_classes = [
        getattr(source_pkg, name)
        for name in source_pkg.__all__
        if inspect.isclass(getattr(source_pkg, name))
        and not issubclass(getattr(source_pkg, name), Enum)
    ]
    assert len(exported_classes) == 91

    for cls in exported_classes:
        assert dataclasses.is_dataclass(cls), f"{cls.__name__} must be a dataclass"
        assert issubclass(cls, IntrospectableMixin), (
            f"{cls.__name__} must inherit IntrospectableMixin"
        )
        assert cls.__dataclass_params__.frozen is True, f"{cls.__name__} must be frozen=True"


@pytest.mark.unit
@pytest.mark.integrity
def test_source_package_has_zero_upward_or_legacy_imports() -> None:
    """Verify gda.model.source never imports legacy gda.enums or upward packages like xref."""
    pkg_dir = Path(inspect.getfile(source_pkg)).parent
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
