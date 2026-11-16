"""Path: src/gda/db/mapper/__init__.py

Public facade and registry for GDA bidirectional SQLite row mappers.

Operational Role:
    Aggregates modular entity row mappers (places, organizations, personas,
    and facts) and exposes the get_mapper() lookup registry.
"""

from __future__ import annotations

from typing import Any

from gda.db.exceptions import EntityMappingError
from gda.db.mapper.base import (
    BaseRowMapper,
    _extract_id_str,
    _extract_year_from_text,
)
from gda.db.mapper.facts import FactRowMapper
from gda.db.mapper.organizations import OrganizationRowMapper
from gda.db.mapper.personas import FamilyRowMapper, IndividualRowMapper
from gda.db.mapper.places import LocationRowMapper, SiteRowMapper
from gda.model.entity.fact import Fact
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.entity.location import Location
from gda.model.entity.organization import Organization
from gda.model.entity.site import Site

__version__ = "1.0.0+build.1"

__all__ = [
    "BaseRowMapper",
    "FactRowMapper",
    "FamilyRowMapper",
    "IndividualRowMapper",
    "LocationRowMapper",
    "OrganizationRowMapper",
    "SiteRowMapper",
    "_extract_id_str",
    "_extract_year_from_text",
    "get_mapper",
]

_MAPPER_REGISTRY: dict[type[Any], BaseRowMapper[Any]] = {
    Location: LocationRowMapper(),
    Site: SiteRowMapper(),
    Organization: OrganizationRowMapper(),
    Individual: IndividualRowMapper(),
    Family: FamilyRowMapper(),
    Fact: FactRowMapper(),
}


def get_mapper[T](model_cls: type[T]) -> BaseRowMapper[T]:
    """Retrieve the registered row mapper for a domain entity class."""
    mapper = _MAPPER_REGISTRY.get(model_cls)
    if mapper is None:
        raise EntityMappingError(
            f"No registered row mapper for entity class '{model_cls.__name__}'.",
            details={"model_cls": model_cls.__name__},
        )
    return mapper
