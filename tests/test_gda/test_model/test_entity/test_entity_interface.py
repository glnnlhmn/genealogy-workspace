"""Path: tests/test_gda/test_model/test_entity/test_entity_interface.py

Architectural contract lock verifying gda.model.entity public facade and invariants.

Operational Role:
    Enforces the exact sealed public interface (__all__) of gda.model.entity,
    verifies BaseEntity and IntrospectableMixin inheritance, validates strict frozen
    Pydantic dataclass configuration, locks mandatory lifecycle/dirty-tracking/serialization
    method contracts across all domain entities, and guards against upward dependency
    leaks into military, xref, or application layers.
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import is_dataclass
from pathlib import Path

import pytest

import gda.model.entity as entity_pkg
from gda.core.introspectable import IntrospectableMixin
from gda.model.base.entity import BaseEntity

__version__ = "2.0.0+build.1"

_EXPECTED_EXPORTS = [
    "Fact",
    "FactParticipant",
    "Family",
    "Individual",
    "Location",
    "Site",
    "SiteEntityModel",
]

_ENTITY_CLASSES = (
    entity_pkg.Fact,
    entity_pkg.Family,
    entity_pkg.Individual,
    entity_pkg.Location,
    entity_pkg.Site,
)

_REQUIRED_ENTITY_MEMBERS = (
    "create",
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
    "mark_dirty",
    "mark_clean",
    "is_dirty",
    "add_note",
    "update_note",
    "delete_note",
    "get_note",
    "find_notes",
    "deprecate",
    "restore",
    "touch",
    "update_urn",
)

_FORBIDDEN_IMPORTS = (
    "gda.enums",
    "gda.model.military",
    "gda.model.xref",
    "gda.entity",
    "gda.manager",
    "gda.db",
    "gda.engine",
    "cli",
    "ancestry_desk",
)


@pytest.mark.smoke
@pytest.mark.integrity
def test_entity_package_exact_public_interface() -> None:
    """Verify gda.model.entity.__all__ matches the exact sorted 7-item public contract."""
    assert hasattr(entity_pkg, "__all__")
    actual = list(entity_pkg.__all__)
    assert actual == _EXPECTED_EXPORTS
    assert actual == sorted(actual)
    for symbol in _EXPECTED_EXPORTS:
        assert hasattr(entity_pkg, symbol), f"gda.model.entity missing exported symbol '{symbol}'"
    assert entity_pkg.SiteEntityModel is entity_pkg.Site


@pytest.mark.unit
@pytest.mark.integrity
def test_entity_classes_inherit_base_entity_and_introspectable() -> None:
    """Verify every domain entity extends BaseEntity and IntrospectableMixin."""
    for cls in _ENTITY_CLASSES:
        assert issubclass(cls, BaseEntity), f"{cls.__name__} must subclass BaseEntity"
        assert issubclass(cls, IntrospectableMixin), (
            f"{cls.__name__} must subclass IntrospectableMixin"
        )
    assert issubclass(entity_pkg.FactParticipant, IntrospectableMixin)


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize(
    "model_cls",
    (*_ENTITY_CLASSES, entity_pkg.FactParticipant),
    ids=lambda c: c.__name__,
)
def test_entity_models_enforce_strict_frozen_pydantic_config(model_cls: type) -> None:
    """Verify all gda.model.entity dataclasses enforce frozen=True, extra='forbid', strict=True."""
    assert is_dataclass(model_cls), f"{model_cls.__name__} must be a dataclass"
    assert model_cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    pydantic_cfg = getattr(model_cls, "__pydantic_config__", {})
    assert pydantic_cfg.get("frozen") is True
    assert pydantic_cfg.get("extra") == "forbid"
    assert pydantic_cfg.get("strict") is True


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize("entity_cls", _ENTITY_CLASSES, ids=lambda c: c.__name__)
def test_entity_classes_implement_required_lifecycle_and_serialization_members(
    entity_cls: type,
) -> None:
    """Verify every entity class exposes the full lifecycle, note, dirty-tracking, and JSON API."""
    for member in _REQUIRED_ENTITY_MEMBERS:
        assert hasattr(entity_cls, member), (
            f"{entity_cls.__name__} missing required member '{member}'"
        )


@pytest.mark.unit
@pytest.mark.integrity
def test_entity_package_has_zero_upward_or_legacy_imports() -> None:
    """Verify gda.model.entity never imports legacy gda.enums or higher-level packages."""
    pkg_dir = Path(inspect.getfile(entity_pkg)).parent
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
