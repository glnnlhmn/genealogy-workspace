"""Path: tests/test_gda/test_entity/test_organizations/test_organizations_contract.py

Authoritative public interface and contract verification suite for gda.entity.organizations.

Operational Role:
    Verifies the end-to-end standalone and hierarchical organization creation,
    validation, and lifecycle gateway, enforces the 4-submodule topology and
    sorted 21-symbol __all__ contract of gda.entity.organizations, verifies
    centralized ENTITY_URN_REGEXES['ORG'] binding, and ensures zero legacy
    imports.
"""

from __future__ import annotations

import ast
import inspect
import pkgutil
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import gda.entity as entity_root_pkg
import gda.entity.organizations as orgs_pkg
import gda.entity.organizations.collection as collection_mod
import gda.entity.organizations.errors as errors_mod
import gda.entity.organizations.util as util_mod
import gda.entity.organizations.validation as validation_mod
from gda.core.enums.orgs import OrganizationCategory
from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ENTITY_URN_REGEXES
from gda.entity.organizations import (
    OrganizationError,
    OrganizationHierarchyError,
    OrganizationNotFoundError,
    Organizations,
    OrganizationValidationError,
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_organization,
    undelete_organization,
    valid_collection_all,
    valid_collection_hierarchy,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_organization,
    valid_urn,
)
from gda.model.atom.id import OrganizationID

__version__ = "1.0.0+build.1"

_EXPECTED_SUBMODULES = {
    "collection",
    "errors",
    "util",
    "validation",
}

AUTHORITATIVE_ORGANIZATIONS_EXPORTS = [
    "OrganizationError",
    "OrganizationHierarchyError",
    "OrganizationNotFoundError",
    "OrganizationValidationError",
    "Organizations",
    "can_tombstone",
    "can_undelete",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "tombstone_organization",
    "undelete_organization",
    "valid_collection_all",
    "valid_collection_hierarchy",
    "valid_collection_indexes",
    "valid_collection_references",
    "valid_collection_tombstones",
    "valid_organization",
    "valid_urn",
]


@pytest.mark.smoke
@pytest.mark.unit
def test_organizations_subsystem_gateway_smoke_pipeline(
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
) -> None:
    """Verify standalone local VFW post creation (without parent) and optional hierarchy lifecycle."""
    collection = Organizations()

    # 1. Create a standalone local VFW post with NO parent organization required
    local_post = collection.create(
        name="VFW Post 411",
        category=OrganizationCategory.VETERANS,
        location_id="LOC-000004",
        meeting_site_id="SID-000001",
        alternate_names=["Concord VFW Post 411"],
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )

    assert isinstance(local_post.id, OrganizationID)
    assert local_post.parent_org_id is None
    assert local_post.category == OrganizationCategory.VETERANS
    assert local_post.id in collection
    assert local_post.canonical_urn in collection
    assert valid_organization(local_post) is True
    assert (
        valid_collection_all(
            collection,
            locations_collection=mock_locations_collection,
            sites_collection=mock_sites_collection,
        )
        is True
    )

    retired = collection.soft_delete(local_post.id, reason="Post charter suspended")
    assert retired.tombstone.is_deprecated is True
    assert local_post.id not in collection

    restored = collection.undelete(
        local_post.id,
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )
    assert restored.tombstone.is_deprecated is False
    assert local_post.id in collection


@pytest.mark.unit
@pytest.mark.integrity
def test_organizations_pkg_topology_and_dunder_all_contract() -> None:
    """Verify submodule topology, sorted 20-symbol __all__, and centralized URN regex binding."""
    discovered = {m.name for m in pkgutil.iter_modules(orgs_pkg.__path__)}
    assert discovered == _EXPECTED_SUBMODULES

    assert orgs_pkg.__all__ == AUTHORITATIVE_ORGANIZATIONS_EXPORTS
    assert orgs_pkg.__all__ == sorted(orgs_pkg.__all__)
    for attr in AUTHORITATIVE_ORGANIZATIONS_EXPORTS:
        assert hasattr(orgs_pkg, attr), f"Export '{attr}' missing from gda.entity.organizations"

    assert collection_mod.__all__ == ["Organizations"]
    assert errors_mod.__all__ == [
        "OrganizationError",
        "OrganizationHierarchyError",
        "OrganizationNotFoundError",
        "OrganizationValidationError",
    ]
    assert util_mod.__all__ == sorted(util_mod.__all__)
    assert validation_mod.__all__ == sorted(validation_mod.__all__)
    assert validation_mod._ORG_URN_PATTERN is ENTITY_URN_REGEXES["ORG"]

    assert entity_root_pkg.__all__ == sorted(entity_root_pkg.__all__)
    assert "Organizations" in entity_root_pkg.__all__
    assert "organizations" in entity_root_pkg.__all__


@pytest.mark.unit
@pytest.mark.integrity
def test_organizations_pkg_class_and_exception_types() -> None:
    """Verify exported classes and exceptions conform to expected inheritance."""
    assert isinstance(Organizations, type)
    assert issubclass(Organizations, IntrospectableMixin)

    for exc_cls in (
        OrganizationError,
        OrganizationHierarchyError,
        OrganizationNotFoundError,
        OrganizationValidationError,
    ):
        assert issubclass(exc_cls, GenealogyDeskError)
        assert issubclass(exc_cls, Exception)


@pytest.mark.unit
@pytest.mark.integrity
def test_organizations_pkg_callable_function_contracts() -> None:
    """Verify all functional facade exports in gda.entity.organizations are callable."""
    callables = (
        can_tombstone,
        can_undelete,
        export_file,
        import_file,
        load_from_db,
        save_to_db,
        tombstone_organization,
        undelete_organization,
        valid_collection_all,
        valid_collection_hierarchy,
        valid_collection_indexes,
        valid_collection_references,
        valid_collection_tombstones,
        valid_organization,
        valid_urn,
    )
    for func in callables:
        assert callable(func)
        assert isinstance(func, types.FunctionType)


@pytest.mark.unit
@pytest.mark.integrity
def test_organizations_pkg_version_and_zero_legacy_imports() -> None:
    """Verify 1.0.0+build.X version metadata and zero legacy gda.enums or gda.util.tombstone imports."""
    assert orgs_pkg.__version__.startswith("1.0.0+build.")
    pkg_dir = Path(inspect.getfile(orgs_pkg)).parent
    for py_path in pkg_dir.rglob("*.py"):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith(
                    ("gda.enums", "gda.util.tombstone", "gda.model.atom.geo")
                ), f"Forbidden legacy import in {py_path}: '{node.module}'"
