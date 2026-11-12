"""Path: src/gda/model/entity/__init__.py

Authoritative domain entity dataclass definitions extending BaseEntity.
"""

from __future__ import annotations

from gda.model.entity.fact import Fact, FactParticipant
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.entity.location import Location
from gda.model.entity.site import Site, SiteEntityModel

__version__ = "2.0.0+build.1"

__all__ = [
    "Fact",
    "FactParticipant",
    "Family",
    "Individual",
    "Location",
    "Site",
    "SiteEntityModel",
]
