"""Path: tests/test_gda/test_entity/test_locations/test_locations_pkg.py

High-level package interface contract and integration smoke test for locations.

Operational Role:
    Verifies that the public API surface exposed by gda.entity.locations adheres
    to architectural contracts, ensuring all expected classes, error types,
    facades, and validation evaluators remain exposed without interface drift.
"""

from __future__ import annotations

import types

import pytest

import gda.entity.locations as loc_pkg
from gda.core.errors import GenealogyDeskError
from gda.entity.locations import (
    LocationError,
    LocationHierarchyError,
    LocationNotFoundError,
    Locations,
    clean_string,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    slugify,
    valid_collection_all,
    valid_collection_cycles,
    valid_collection_indexes,
    valid_collection_patterns,
    valid_collection_roots,
    valid_collection_tombstones,
    valid_display_text,
    valid_hierarchy,
    valid_urn,
)
from gda.enums.location import JurisdictionCategory
from gda.model.atom.id import LocationID

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: SUBSYSTEM GATEWAY SMOKE TEST
# ==============================================================================


@pytest.mark.smoke
def test_locations_subsystem_gateway_smoke_pipeline(
    empty_collection: Locations,
) -> None:
    """Verify primary end-to-end gateway: hierarchy creation, indexing, and health validation."""
    leaf = empty_collection.create_hierarchy(
        country="United States",
        state="New Hampshire",
        county="Merrimack",
        township="Bow",
        local="Bow Center",
    )

    assert isinstance(leaf.id, LocationID)
    assert leaf.category == JurisdictionCategory.MUNICIPALITY
    assert (
        leaf.canonical_urn
        == "urn:gda:loc:united_states:new_hampshire:merrimack:bow:bow_center"
    )
    assert len(empty_collection) == 5
    assert leaf.id in empty_collection
    assert leaf.canonical_urn in empty_collection

    assert valid_collection_all(empty_collection) is True


# ==============================================================================
# GROUP 2: PUBLIC PACKAGE EXPORTS & INTERFACE CONTRACTS
# ==============================================================================


@pytest.mark.regression
def test_locations_pkg_module_dunder_all_contract() -> None:
    """Verify __all__ contains the complete authoritative list of public exports."""
    expected_exports = {
        "LocationError",
        "LocationHierarchyError",
        "LocationNotFoundError",
        "Locations",
        "clean_string",
        "export_file",
        "import_file",
        "load_from_db",
        "save_to_db",
        "slugify",
        "valid_collection_all",
        "valid_collection_cycles",
        "valid_collection_indexes",
        "valid_collection_patterns",
        "valid_collection_roots",
        "valid_collection_tombstones",
        "valid_display_text",
        "valid_hierarchy",
        "valid_urn",
    }
    assert set(loc_pkg.__all__) == expected_exports
    for attr in expected_exports:
        assert hasattr(loc_pkg, attr), (
            f"Export '{attr}' missing from gda.entity.locations"
        )


@pytest.mark.regression
def test_locations_pkg_class_and_exception_types() -> None:
    """Verify exported classes conform to expected inheritance and type hierarchies."""
    assert isinstance(Locations, type)

    for exc_cls in (LocationError, LocationNotFoundError, LocationHierarchyError):
        assert issubclass(exc_cls, GenealogyDeskError)
        assert issubclass(exc_cls, Exception)


@pytest.mark.regression
def test_locations_pkg_callable_function_contracts() -> None:
    """Verify all functional facade exports are callable objects."""
    callables = (
        clean_string,
        export_file,
        import_file,
        load_from_db,
        save_to_db,
        slugify,
        valid_collection_all,
        valid_collection_cycles,
        valid_collection_indexes,
        valid_collection_patterns,
        valid_collection_roots,
        valid_collection_tombstones,
        valid_display_text,
        valid_hierarchy,
        valid_urn,
    )
    for func in callables:
        assert callable(func)
        assert isinstance(func, types.FunctionType)


@pytest.mark.regression
def test_locations_pkg_version_metadata() -> None:
    """Verify the package exports a compliant PEP 440 __version__ string."""
    assert hasattr(loc_pkg, "__version__")
    assert isinstance(loc_pkg.__version__, str)
    assert "+build." in loc_pkg.__version__
