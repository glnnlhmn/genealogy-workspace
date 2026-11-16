"""Path: tests/test_gda/test_db/test_mapper/test_mapper_contract.py

Interface contract and registry verification test suite for gda.db.mapper (__init__.py).

Operational Role:
    1:1 verification suite for src/gda/db/mapper/__init__.py. Validates __all__
    exports, alphabetical sorting, get_mapper() dispatching across all 6 core
    domain entities, and EntityMappingError on unknown entity classes.
"""

from __future__ import annotations

import pytest

import gda.db.mapper as mapper_pkg
from gda.db.exceptions import EntityMappingError
from gda.db.mapper import (
    FactRowMapper,
    FamilyRowMapper,
    IndividualRowMapper,
    LocationRowMapper,
    OrganizationRowMapper,
    SiteRowMapper,
    get_mapper,
)
from gda.model.entity.fact import Fact
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.entity.location import Location
from gda.model.entity.organization import Organization
from gda.model.entity.site import Site

__version__ = "1.0.0+build.1"


@pytest.mark.unit
def test_mapper_package_dunder_all_and_registry_contract() -> None:
    """Verify gda.db.mapper.__all__ is sorted and get_mapper resolves all 6 core entities."""
    assert mapper_pkg.__all__ == sorted(mapper_pkg.__all__)
    assert isinstance(get_mapper(Location), LocationRowMapper)
    assert isinstance(get_mapper(Site), SiteRowMapper)
    assert isinstance(get_mapper(Organization), OrganizationRowMapper)
    assert isinstance(get_mapper(Individual), IndividualRowMapper)
    assert isinstance(get_mapper(Family), FamilyRowMapper)
    assert isinstance(get_mapper(Fact), FactRowMapper)


@pytest.mark.regression
def test_get_mapper_unregistered_class_raises_entity_mapping_error() -> None:
    """Verify get_mapper raises EntityMappingError when given an unregistered class."""

    class UnregisteredEntity:
        pass

    with pytest.raises(EntityMappingError, match="No registered row mapper"):
        get_mapper(UnregisteredEntity)  # type: ignore[arg-type]
