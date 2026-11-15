"""Path: tests/test_gda/test_entity/test_sites/test_sites_contract.py

Authoritative public interface and contract verification suite for gda.entity.sites.

Operational Role:
    Verifies the end-to-end site creation, validation, and lifecycle gateway,
    enforces the 4-submodule topology and sorted 19-symbol __all__ contract of
    gda.entity.sites, verifies centralized ENTITY_URN_REGEXES['SID'] binding,
    and ensures zero legacy gda.enums or gda.util.tombstone imports.
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
import gda.entity.sites as sites_pkg
import gda.entity.sites.collection as collection_mod
import gda.entity.sites.errors as errors_mod
import gda.entity.sites.util as util_mod
import gda.entity.sites.validation as validation_mod
from gda.core.enums.site import SiteType
from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ENTITY_URN_REGEXES
from gda.entity.sites import (
    SiteError,
    SiteNotFoundError,
    Sites,
    SiteValidationError,
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_site,
    undelete_site,
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_locations,
    valid_collection_tombstones,
    valid_site,
    valid_site_address,
    valid_urn,
)
from gda.model.atom.id import SiteID

__version__ = "1.0.0+build.3"

_EXPECTED_SUBMODULES = {
    "collection",
    "errors",
    "util",
    "validation",
}

AUTHORITATIVE_SITES_EXPORTS = [
    "SiteError",
    "SiteNotFoundError",
    "SiteValidationError",
    "Sites",
    "can_tombstone",
    "can_undelete",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "tombstone_site",
    "undelete_site",
    "valid_collection_all",
    "valid_collection_indexes",
    "valid_collection_locations",
    "valid_collection_tombstones",
    "valid_site",
    "valid_site_address",
    "valid_urn",
]


@pytest.mark.smoke
@pytest.mark.unit
def test_sites_subsystem_gateway_smoke_pipeline(
    mock_locations_collection: MagicMock,
) -> None:
    """Verify end-to-end site creation, lookup, validation, retirement, and restoration."""
    collection = Sites()
    site = collection.create(
        name="Evans Cemetery",
        category=SiteType.CEMETERY,
        location_id="LOC-000004",
        alternate_names=["Evans Burying Ground"],
        locations_collection=mock_locations_collection,
    )

    assert isinstance(site.id, SiteID)
    assert site.category == SiteType.CEMETERY
    assert site.id in collection
    assert site.canonical_urn in collection
    assert valid_site(site) is True
    assert (
        valid_collection_all(
            collection,
            locations_collection=mock_locations_collection,
        )
        is True
    )

    retired = collection.soft_delete(site.id, reason="Merged record")
    assert retired.tombstone.is_deprecated is True
    assert site.id not in collection

    restored = collection.undelete(
        site.id,
        locations_collection=mock_locations_collection,
    )
    assert restored.tombstone.is_deprecated is False
    assert site.id in collection


@pytest.mark.unit
@pytest.mark.integrity
def test_sites_pkg_topology_and_dunder_all_contract() -> None:
    """Verify submodule topology, sorted 19-symbol __all__, and centralized URN regex binding."""
    discovered = {m.name for m in pkgutil.iter_modules(sites_pkg.__path__)}
    assert discovered == _EXPECTED_SUBMODULES

    assert sites_pkg.__all__ == AUTHORITATIVE_SITES_EXPORTS
    assert sites_pkg.__all__ == sorted(sites_pkg.__all__)
    for attr in AUTHORITATIVE_SITES_EXPORTS:
        assert hasattr(sites_pkg, attr), f"Export '{attr}' missing from gda.entity.sites"

    assert collection_mod.__all__ == ["Sites"]
    assert errors_mod.__all__ == [
        "SiteError",
        "SiteNotFoundError",
        "SiteValidationError",
    ]
    assert util_mod.__all__ == sorted(util_mod.__all__)
    assert validation_mod.__all__ == sorted(validation_mod.__all__)
    assert validation_mod._SITE_URN_PATTERN is ENTITY_URN_REGEXES["SID"]

    assert entity_root_pkg.__all__ == sorted(entity_root_pkg.__all__)
    assert "Sites" in entity_root_pkg.__all__
    assert "sites" in entity_root_pkg.__all__


@pytest.mark.unit
@pytest.mark.integrity
def test_sites_pkg_class_and_exception_types() -> None:
    """Verify exported classes and exceptions conform to expected inheritance."""
    assert isinstance(Sites, type)
    assert issubclass(Sites, IntrospectableMixin)

    for exc_cls in (SiteError, SiteNotFoundError, SiteValidationError):
        assert issubclass(exc_cls, GenealogyDeskError)
        assert issubclass(exc_cls, Exception)


@pytest.mark.unit
@pytest.mark.integrity
def test_sites_pkg_callable_function_contracts() -> None:
    """Verify all functional facade exports in gda.entity.sites are callable."""
    callables = (
        can_tombstone,
        can_undelete,
        export_file,
        import_file,
        load_from_db,
        save_to_db,
        tombstone_site,
        undelete_site,
        valid_collection_all,
        valid_collection_indexes,
        valid_collection_locations,
        valid_collection_tombstones,
        valid_site,
        valid_site_address,
        valid_urn,
    )
    for func in callables:
        assert callable(func)
        assert isinstance(func, types.FunctionType)


@pytest.mark.unit
@pytest.mark.integrity
def test_sites_pkg_version_and_zero_legacy_imports() -> None:
    """Verify 1.0.0+build.X version metadata and zero legacy gda.enums or gda.util.tombstone imports."""
    assert sites_pkg.__version__.startswith("1.0.0+build.")
    pkg_dir = Path(inspect.getfile(sites_pkg)).parent
    for py_path in pkg_dir.rglob("*.py"):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith(
                    ("gda.enums", "gda.util.tombstone", "gda.model.atom.geo")
                ), f"Forbidden legacy import in {py_path}: '{node.module}'"
