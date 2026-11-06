"""Path: tests/test_gda/test_entity/test_locations/test_errors.py

Comprehensive test suite verifying location subsystem exception contracts.

Operational Role:
    Verifies default error codes, custom details payload propagation, inheritance
    relationships anchored to GenealogyDeskError, and string representations across
    LocationError, LocationNotFoundError, and LocationHierarchyError.
"""

from __future__ import annotations

import pytest

from gda.core.errors import GenealogyDeskError
from gda.entity.locations.errors import (
    LocationError,
    LocationHierarchyError,
    LocationNotFoundError,
)

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: BASE EXCEPTION CONTRACTS (LocationError)
# ==============================================================================


@pytest.mark.smoke
def test_location_error_default_instantiation() -> None:
    """Verify LocationError instantiates with default error code and message."""
    err = LocationError("Base location exception occurred.")
    assert str(err) == "Base location exception occurred."
    assert err.error_code == "ERR_LOCATION"
    assert err.details == {}
    assert isinstance(err, GenealogyDeskError)


@pytest.mark.unit
def test_location_error_custom_parameters() -> None:
    """Verify LocationError retains custom error code and diagnostic details."""
    details = {"field": "canonical_urn", "value": "invalid_urn"}
    err = LocationError(
        message="Custom location failure.",
        error_code="ERR_CUSTOM_LOC",
        details=details,
    )
    assert err.error_code == "ERR_CUSTOM_LOC"
    assert err.details == details


@pytest.mark.regression
def test_location_error_inheritance_hierarchy() -> None:
    """Verify LocationError is a direct subclass of GenealogyDeskError."""
    assert issubclass(LocationError, GenealogyDeskError)
    assert issubclass(LocationError, Exception)


# ==============================================================================
# GROUP 2: ENTITY LOOKUP EXCEPTIONS (LocationNotFoundError)
# ==============================================================================


@pytest.mark.regression
def test_location_not_found_error_default_instantiation() -> None:
    """Verify LocationNotFoundError assigns default ERR_LOCATION_NOT_FOUND code."""
    err = LocationNotFoundError("Target location not found.")
    assert str(err) == "Target location not found."
    assert err.error_code == "ERR_LOCATION_NOT_FOUND"
    assert err.details == {}
    assert isinstance(err, LocationError)


@pytest.mark.regression
def test_location_not_found_error_custom_parameters() -> None:
    """Verify LocationNotFoundError supports custom error codes and diagnostic details."""
    details = {"lookup_key": "LOC-999999"}
    err = LocationNotFoundError(
        message="Missing location key.",
        error_code="ERR_CUSTOM_NOT_FOUND",
        details=details,
    )
    assert err.error_code == "ERR_CUSTOM_NOT_FOUND"
    assert err.details == details


@pytest.mark.regression
def test_location_not_found_error_inheritance_hierarchy() -> None:
    """Verify LocationNotFoundError inherits from LocationError and GenealogyDeskError."""
    assert issubclass(LocationNotFoundError, LocationError)
    assert issubclass(LocationNotFoundError, GenealogyDeskError)


# ==============================================================================
# GROUP 3: JURISDICTIONAL HIERARCHY EXCEPTIONS (LocationHierarchyError)
# ==============================================================================


@pytest.mark.regression
def test_location_hierarchy_error_default_instantiation() -> None:
    """Verify LocationHierarchyError assigns default ERR_LOCATION_HIERARCHY code."""
    err = LocationHierarchyError("Invalid jurisdictional hierarchy link.")
    assert str(err) == "Invalid jurisdictional hierarchy link."
    assert err.error_code == "ERR_LOCATION_HIERARCHY"
    assert err.details == {}
    assert isinstance(err, LocationError)


@pytest.mark.regression
def test_location_hierarchy_error_custom_parameters() -> None:
    """Verify LocationHierarchyError retains custom codes and diagnostic details."""
    details = {"parent_id": "LOC-000001", "child_id": "LOC-000005"}
    err = LocationHierarchyError(
        message="Illegal tier skip detected.",
        error_code="ERR_CUSTOM_HIERARCHY",
        details=details,
    )
    assert err.error_code == "ERR_CUSTOM_HIERARCHY"
    assert err.details == details


@pytest.mark.regression
def test_location_hierarchy_error_inheritance_hierarchy() -> None:
    """Verify LocationHierarchyError inherits from LocationError and GenealogyDeskError."""
    assert issubclass(LocationHierarchyError, LocationError)
    assert issubclass(LocationHierarchyError, GenealogyDeskError)


# ==============================================================================
# GROUP 4: EXCEPTION POLYMORPHISM & HANDLING
# ==============================================================================


@pytest.mark.regression
def test_polymorphic_exception_handling_catch_by_base() -> None:
    """Verify derived location exceptions are caught by LocationError and GenealogyDeskError."""
    try:
        raise LocationNotFoundError("Entity missing.")
    except LocationError as exc:
        assert isinstance(exc, LocationNotFoundError)

    try:
        raise LocationHierarchyError("Cyclic link.")
    except GenealogyDeskError as exc:
        assert isinstance(exc, LocationHierarchyError)


@pytest.mark.regression
def test_exception_representation_string() -> None:
    """Verify string representation of location exceptions contains verbatim message."""
    err = LocationHierarchyError("Cycle detected: LOC-1 -> LOC-2 -> LOC-1")
    assert "Cycle detected" in str(err)
