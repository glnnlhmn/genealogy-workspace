"""Path: src/gda/repository/xref/__init__.py

SQLite repositories for Cross-Reference (gda.model.xref) bridge and index models.
"""

from __future__ import annotations

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

__version__ = "1.0.0+build.2"

__all__ = [
    "FactParticipantXRefRepository",
    "IndividualFamilyXRefRepository",
    "IndividualOrganizationXRefRepository",
    "IndividualSourceXRefRepository",
    "IndividualSurnameXRefRepository",
    "LocationXRefRepository",
    "MediaXRefRepository",
    "SiteXRefRepository",
    "SurnameXRefRepository",
]
