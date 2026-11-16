"""Path: src/gda/model/entity/__init__.py

Authoritative domain entity dataclass definitions extending BaseEntity.

Operational Role:
    Unified public export facade for core genealogical domain entities:
    Fact, FactParticipant, Family, Individual, Location, Organization
    (with backward-compatibility alias OrganizationEntityModel), and Site
    (with backward-compatibility alias SiteEntityModel).
"""

from __future__ import annotations

from gda.model.entity.fact import Fact, FactParticipant
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.entity.location import Location
from gda.model.entity.organization import Organization, OrganizationEntityModel
from gda.model.entity.site import Site, SiteEntityModel

__version__ = "1.0.0+build.3"

__all__ = [
    "Fact",  # fact.py
    "FactParticipant",  # fact.py
    "Family",  # family.py
    "Individual",  # individual.py
    "Location",  # location.py
    "Organization",  # organization.py
    "OrganizationEntityModel",  # organization.py
    "Site",  # site.py
    "SiteEntityModel",  # site.py
]
