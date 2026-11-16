"""Path: tests/test_gda/test_entity/test_locations/test_locations_contract.py

Authoritative public interface and contract verification suite for gda.entity.locations.

Operational Role:
    Verifies the end-to-end 5-tier jurisdictional pipeline, enforces the
    4-submodule topology and sorted 26-symbol __all__ contract of
    gda.entity.locations, verifies centralized ENTITY_URN_REGEXES['LOC']
    binding, and ensures zero legacy gda.enums imports.
"""

from __future__ import annotations

import ast
import inspect
import pkgutil
import types
from pathlib import Path

import pytest

import gda.entity as entity_root_pkg
import gda.entity.locations as locations_pkg
import gda.entity.locations.collection as collection_mod
import gda.entity.locations.errors as errors_mod
import gda.entity.locations.util as util_mod
import gda.entity.locations.validation as validation_mod
from gda.core.enums.location import JurisdictionCategory
from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ENTITY_URN_REGEXES
from gda.entity.locations import (
    LocationError,
    LocationHierarchyError,
    LocationNotFoundError,
    Locations,
    build_jurisdiction_hierarchy,
    can_tombstone,
    can_undelete,
    clean_string,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    slugify,
    tombstone_location,
    undelete_location,
    valid_collection_all,
    valid_collection_cycles,
    valid_collection_indexes,
    valid_collection_patterns,
    valid_collection_roots,
    valid_collection_tombstones,
    valid_display_text,
    valid_hierarchy,
    valid_urn,
    validate_urn_tier_sequence,
)
from gda.model.atom.id import LocationID

__version__ = "1.0.0+build.3"

_EXPECTED_SUBMODULES = {
    "collection",
    "errors",
    "util",
    "validation",
}

AUTHORITATIVE_LOCATIONS_EXPORTS = [
    "LocationError",
    "LocationHierarchyError",
    "LocationNotFoundError",
    "Locations",
    "build_jurisdiction_hierarchy",
    "can_tombstone",
    "can_undelete",
    "clean_string",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "slugify",
    "tombstone_location",
    "undelete_location",
    "valid_collection_all",
    "valid_collection_cycles",
    "valid_collection_indexes",
    "valid_collection_patterns",
    "valid_collection_roots",
    "valid_collection_tombstones",
    "valid_display_text",
    "valid_hierarchy",
    "valid_urn",
    "validate_urn_tier_sequence",
]


@pytest.mark.smoke
@pytest.mark.unit
def test_locations_subsystem_gateway_smoke_pipeline(
    empty_collection: Locations,
) -> None:
    """Verify end-to-end 5-tier hierarchy creation, lookup, URN validation, retirement, and undelete."""
    leaf = empty_collection.create_hierarchy(
        country="United States",
        state="New Hampshire",
        county="Merrimack",
        township="Bow",
        local="Bow Center",
    )

    assert isinstance(leaf.id, LocationID)
    assert leaf.category == JurisdictionCategory.MUNICIPALITY
    assert valid_urn(leaf.canonical_urn, leaf.category) is True
    assert valid_collection_all(empty_collection) is True
    assert len(empty_collection) == 5

    retired = empty_collection.soft_delete(leaf.id, reason="Smoke pipeline retirement")
    assert retired.tombstone.is_deprecated is True
    assert leaf.id not in empty_collection

    restored = empty_collection.undelete(leaf.id)
    assert restored.tombstone.is_deprecated is False
    assert leaf.id in empty_collection


@pytest.mark.unit
@pytest.mark.integrity
def test_locations_pkg_topology_and_dunder_all_contract() -> None:
    """Verify submodule topology, sorted 26-symbol __all__, and centralized URN regex binding."""
    discovered = {m.name for m in pkgutil.iter_modules(locations_pkg.__path__)}
    assert discovered == _EXPECTED_SUBMODULES

    assert locations_pkg.__all__ == AUTHORITATIVE_LOCATIONS_EXPORTS
    assert locations_pkg.__all__ == sorted(locations_pkg.__all__)
    for attr in AUTHORITATIVE_LOCATIONS_EXPORTS:
        assert hasattr(locations_pkg, attr), f"Export '{attr}' missing from gda.entity.locations"

    assert collection_mod.__all__ == ["Locations"]
    assert errors_mod.__all__ == [
        "LocationError",
        "LocationHierarchyError",
        "LocationNotFoundError",
    ]
    assert util_mod.__all__ == sorted(util_mod.__all__)
    assert validation_mod.__all__ == sorted(validation_mod.__all__)
    assert validation_mod._LOCATION_URN_PATTERN is ENTITY_URN_REGEXES["LOC"]

    assert entity_root_pkg.__all__ == sorted(entity_root_pkg.__all__)
    assert "Locations" in entity_root_pkg.__all__
    assert "locations" in entity_root_pkg.__all__


@pytest.mark.unit
@pytest.mark.integrity
def test_locations_pkg_class_and_exception_types() -> None:
    """Verify exported classes and exceptions conform to expected inheritance."""
    assert isinstance(Locations, type)
    assert issubclass(Locations, IntrospectableMixin)

    for exc_cls in (LocationError, LocationHierarchyError, LocationNotFoundError):
        assert issubclass(exc_cls, GenealogyDeskError)
        assert issubclass(exc_cls, Exception)


@pytest.mark.unit
@pytest.mark.integrity
def test_locations_pkg_callable_function_contracts() -> None:
    """Verify all functional facade exports in gda.entity.locations are callable."""
    callables = (
        build_jurisdiction_hierarchy,
        can_tombstone,
        can_undelete,
        clean_string,
        export_file,
        import_file,
        load_from_db,
        save_to_db,
        slugify,
        tombstone_location,
        undelete_location,
        valid_collection_all,
        valid_collection_cycles,
        valid_collection_indexes,
        valid_collection_patterns,
        valid_collection_roots,
        valid_collection_tombstones,
        valid_display_text,
        valid_hierarchy,
        valid_urn,
        validate_urn_tier_sequence,
    )
    for func in callables:
        assert callable(func)
        assert isinstance(func, types.FunctionType)


@pytest.mark.unit
@pytest.mark.integrity
def test_locations_pkg_version_and_zero_legacy_imports() -> None:
    """Verify 1.0.0+build.X version metadata and zero legacy gda.enums imports."""
    assert locations_pkg.__version__.startswith("1.0.0+build.")
    pkg_dir = Path(inspect.getfile(locations_pkg)).parent
    for py_path in pkg_dir.rglob("*.py"):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith(("gda.enums", "gda.util.tombstone")), (
                    f"Forbidden legacy import in {py_path}: '{node.module}'"
                )
