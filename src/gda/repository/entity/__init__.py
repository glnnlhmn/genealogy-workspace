"""Path: src/gda/repository/entity/__init__.py

SQLite repositories for the 6 core GDA entities (Location, Site, Organization,
Individual, Family, and Fact).
"""

from __future__ import annotations

from gda.repository.entity.repository import (
    FactRepository,
    FamilyRepository,
    IndividualRepository,
    LocationRepository,
    OrganizationRepository,
    SiteRepository,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "FactRepository",
    "FamilyRepository",
    "IndividualRepository",
    "LocationRepository",
    "OrganizationRepository",
    "SiteRepository",
]
