"""Path: src/gda/repository/xref/__init__.py

SQLite repositories and in-memory collections for Cross-Reference (gda.model.xref)
bridge and index models.
"""

from __future__ import annotations

from gda.repository.xref.collection import (
    BaseXRefCollection,
    FactParticipantXRefCollection,
    IndividualFamilyXRefCollection,
    IndividualOrganizationXRefCollection,
    IndividualSourceXRefCollection,
    IndividualSurnameXRefCollection,
    LocationXRefCollection,
    MediaXRefCollection,
    SiteXRefCollection,
    SurnameXRefCollection,
)
from gda.repository.xref.repository import (
    FactParticipantXRefRepository,
    IndividualFamilyXRefRepository,
    IndividualOrganizationXRefRepository,
    IndividualSourceXRefRepository,
    IndividualSurnameXRefRepository,
    LocationXRefRepository,
    MediaXRefRepository,
    SiteXRefRepository,
    SurnameXRefRepository,
)

__version__ = "1.0.0+build.3"

__all__ = [
    "BaseXRefCollection",
    "FactParticipantXRefCollection",
    "FactParticipantXRefRepository",
    "IndividualFamilyXRefCollection",
    "IndividualFamilyXRefRepository",
    "IndividualOrganizationXRefCollection",
    "IndividualOrganizationXRefRepository",
    "IndividualSourceXRefCollection",
    "IndividualSourceXRefRepository",
    "IndividualSurnameXRefCollection",
    "IndividualSurnameXRefRepository",
    "LocationXRefCollection",
    "LocationXRefRepository",
    "MediaXRefCollection",
    "MediaXRefRepository",
    "SiteXRefCollection",
    "SiteXRefRepository",
    "SurnameXRefCollection",
    "SurnameXRefRepository",
]
