"""Path: src/gda/model/atom/__init__.py

Atomic identification, temporal, metric, and spatial primitives package.
"""

from __future__ import annotations

from gda.model.atom.date import (
    BirthYear,
    CensusYear,
    CensusYearEnum,
    DateModifier,
    DateString,
    DeathYear,
    EventDate,
    EventDateRange,
    HistoricalYear,
    IsoTimestamp,
)
from gda.model.atom.geo import (
    Coordinates,
    Latitude,
    Longitude,
)
from gda.model.atom.id import (
    AtomID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    MediaID,
    NoteID,
    RepositoryID,
    SiteID,
    SourceID,
    TranscriptID,
    UUIDv4Str,
)
from gda.model.atom.scalar import (
    AhnentafelNumber,
    ConfidenceScore,
    NewsCategoryCode,
    PubCode,
    QuayScore,
)

__version__ = "1.0.0+build.10"

__all__ = [
    "AhnentafelNumber",
    "AtomID",
    "BirthYear",
    "CensusYear",
    "CensusYearEnum",
    "ConfidenceScore",
    "Coordinates",
    "DateModifier",
    "DateString",
    "DeathYear",
    "EventDate",
    "EventDateRange",
    "FactID",
    "FamilyID",
    "HistoricalYear",
    "IndividualID",
    "IsoTimestamp",
    "Latitude",
    "LocationID",
    "Longitude",
    "MediaID",
    "NewsCategoryCode",
    "NoteID",
    "PubCode",
    "QuayScore",
    "RepositoryID",
    "SiteID",
    "SourceID",
    "TranscriptID",
    "UUIDv4Str",
]
