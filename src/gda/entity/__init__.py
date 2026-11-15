"""Path: src/gda/entity/__init__.py

Domain entity collection managers, validation services, and persistence gateways.

Operational Role:
    Top-level package facade for in-memory domain entity managers and
    relational collection authorities. Exports completed and verified Phase 6
    entity manager subpackages (Batches 1-6: locations, sites, organizations,
    facts, individuals, families).
"""

from __future__ import annotations

from gda.entity import (
    facts,
    families,
    individuals,
    locations,
    organizations,
    sites,
)
from gda.entity.facts import (
    FactError,
    FactNotFoundError,
    Facts,
    FactValidationError,
)
from gda.entity.families import (
    Families,
    FamilyError,
    FamilyNotFoundError,
    FamilyValidationError,
)
from gda.entity.individuals import (
    IndividualError,
    IndividualNotFoundError,
    Individuals,
    IndividualValidationError,
)
from gda.entity.locations import (
    LocationError,
    LocationHierarchyError,
    LocationNotFoundError,
    Locations,
)
from gda.entity.organizations import (
    OrganizationError,
    OrganizationHierarchyError,
    OrganizationNotFoundError,
    Organizations,
    OrganizationValidationError,
)
from gda.entity.sites import (
    SiteError,
    SiteNotFoundError,
    Sites,
    SiteValidationError,
)

__version__ = "1.0.0+build.7"

__all__ = [
    "FactError",  # facts
    "FactNotFoundError",  # facts
    "FactValidationError",  # facts
    "Facts",  # facts
    "Families",  # families
    "FamilyError",  # families
    "FamilyNotFoundError",  # families
    "FamilyValidationError",  # families
    "IndividualError",  # individuals
    "IndividualNotFoundError",  # individuals
    "IndividualValidationError",  # individuals
    "Individuals",  # individuals
    "LocationError",  # locations
    "LocationHierarchyError",  # locations
    "LocationNotFoundError",  # locations
    "Locations",  # locations
    "OrganizationError",  # organizations
    "OrganizationHierarchyError",  # organizations
    "OrganizationNotFoundError",  # organizations
    "OrganizationValidationError",  # organizations
    "Organizations",  # organizations
    "SiteError",  # sites
    "SiteNotFoundError",  # sites
    "SiteValidationError",  # sites
    "Sites",  # sites
    "facts",  # subpackage
    "families",  # subpackage
    "individuals",  # subpackage
    "locations",  # subpackage
    "organizations",  # subpackage
    "sites",  # subpackage
]
