"""Path: tests/test_gda/test_entity/conftest.py

Shared directory-scoped test fixtures for all gda.entity subpackage test suites.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

__version__ = "1.0.0+build.2"


@pytest.fixture
def mock_locations_collection() -> MagicMock:
    """Return a mock Locations collection accepting LOC-000001 and LOC-000004."""
    mock_coll = MagicMock()
    mock_coll.__contains__.side_effect = lambda item: (
        str(item)
        in {
            "LOC-000001",
            "LOC-000004",
        }
    )
    return mock_coll


@pytest.fixture
def mock_sites_collection() -> MagicMock:
    """Return a mock Sites collection accepting SID-000001 and SID-000002."""
    mock_coll = MagicMock()
    mock_coll.__contains__.side_effect = lambda item: (
        str(item)
        in {
            "SID-000001",
            "SID-000002",
        }
    )
    return mock_coll


@pytest.fixture
def mock_organizations_collection() -> MagicMock:
    """Return a mock Organizations collection accepting ORG-000001 and ORG-000002."""
    mock_coll = MagicMock()
    mock_coll.__contains__.side_effect = lambda item: (
        str(item)
        in {
            "ORG-000001",
            "ORG-000002",
        }
    )
    return mock_coll


@pytest.fixture
def mock_individuals_collection() -> MagicMock:
    """Return a mock Individuals collection accepting IND-000001, IND-000002, IND-000003, and IND-000010."""
    mock_coll = MagicMock()
    mock_coll.__contains__.side_effect = lambda item: (
        str(item)
        in {
            "IND-000001",
            "IND-000002",
            "IND-000003",
            "IND-000010",
        }
    )
    return mock_coll


@pytest.fixture
def mock_families_collection() -> MagicMock:
    """Return a mock Families collection accepting FAM-000001 and FAM-000002."""
    mock_coll = MagicMock()
    mock_coll.__contains__.side_effect = lambda item: (
        str(item)
        in {
            "FAM-000001",
            "FAM-000002",
        }
    )
    return mock_coll


@pytest.fixture
def mock_facts_collection() -> MagicMock:
    """Return a mock Facts collection accepting FID-000001 and FID-000002."""
    mock_coll = MagicMock()
    mock_coll.__contains__.side_effect = lambda item: (
        str(item)
        in {
            "FID-000001",
            "FID-000002",
        }
    )
    return mock_coll
