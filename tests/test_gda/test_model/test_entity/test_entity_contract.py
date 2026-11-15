"""Path: tests/test_gda/test_model/test_entity/test_entity_contract.py

Authoritative public interface and contract verification suite for gda.model.entity.

Operational Role:
    Freezes and validates the 6-submodule topology, 9-symbol __all__ facade,
    submodule __all__ exports, centralized ENTITY_ID_REGEXES integration from
    gda.core.types, BaseEntity and IntrospectableMixin inheritance, strict
    frozen Pydantic dataclass configuration, mandatory lifecycle/dirty-tracking/
    serialization method contracts, and zero upward dependency leaks.
"""

from __future__ import annotations

import ast
import inspect
import pkgutil
from dataclasses import is_dataclass
from pathlib import Path

import pytest

import gda.model.entity as entity_pkg
import gda.model.entity.fact as fact_mod
import gda.model.entity.family as family_mod
import gda.model.entity.individual as individual_mod
import gda.model.entity.location as location_mod
import gda.model.entity.organization as organization_mod
import gda.model.entity.site as site_mod
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ENTITY_ID_REGEXES
from gda.model.base.entity import BaseEntity

__version__ = "1.0.0+build.3"

_EXPECTED_SUBMODULES = {
    "fact",
    "family",
    "individual",
    "location",
    "organization",
    "site",
}

AUTHORITATIVE_ENTITY_EXPORTS = [
    "Fact",
    "FactParticipant",
    "Family",
    "Individual",
    "Location",
    "Organization",
    "OrganizationEntityModel",
    "Site",
    "SiteEntityModel",
]

_ENTITY_CLASSES = (
    entity_pkg.Fact,
    entity_pkg.Family,
    entity_pkg.Individual,
    entity_pkg.Location,
    entity_pkg.Organization,
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
    "gda.model.source.military",
    "gda.model.source.orgs",
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
def test_entity_package_exact_public_interface_and_submodules() -> None:
    """Verify gda.model.entity submodule topology and sorted 9-item __all__ contract."""
    discovered = {m.name for m in pkgutil.iter_modules(entity_pkg.__path__)}
    assert discovered == _EXPECTED_SUBMODULES

    actual = list(entity_pkg.__all__)
    assert actual == AUTHORITATIVE_ENTITY_EXPORTS
    assert actual == sorted(actual)
    for symbol in AUTHORITATIVE_ENTITY_EXPORTS:
        assert hasattr(entity_pkg, symbol), f"gda.model.entity missing exported symbol '{symbol}'"
    assert entity_pkg.OrganizationEntityModel is entity_pkg.Organization
    assert entity_pkg.SiteEntityModel is entity_pkg.Site

    assert fact_mod.__all__ == ["Fact", "FactParticipant"]
    assert family_mod.__all__ == ["Family"]
    assert individual_mod.__all__ == ["Individual"]
    assert location_mod.__all__ == ["Location"]
    assert organization_mod.__all__ == ["Organization", "OrganizationEntityModel"]
    assert site_mod.__all__ == ["Site", "SiteEntityModel"]


@pytest.mark.unit
@pytest.mark.integrity
def test_entity_classes_use_centralized_core_types_id_regexes() -> None:
    """Verify every domain entity binds _ID_PATTERN directly from gda.core.types.ENTITY_ID_REGEXES."""
    assert entity_pkg.Fact._ID_PATTERN is ENTITY_ID_REGEXES["FID"]
    assert entity_pkg.Family._ID_PATTERN is ENTITY_ID_REGEXES["FAM"]
    assert entity_pkg.Individual._ID_PATTERN is ENTITY_ID_REGEXES["IND"]
    assert entity_pkg.Location._ID_PATTERN is ENTITY_ID_REGEXES["LOC"]
    assert entity_pkg.Organization._ID_PATTERN is ENTITY_ID_REGEXES["ORG"]
    assert entity_pkg.Site._ID_PATTERN is ENTITY_ID_REGEXES["SID"]


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
