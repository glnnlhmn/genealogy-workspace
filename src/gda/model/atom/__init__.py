"""Path: src/gda/model/atom/__init__.py

Atomic identification, temporal, metric, and spatial primitives package.

Operational Role:
    Exposes immutable foundational atoms representing identifiers, calendar dates,
    geospatial coordinates, scalar values, and archival URN references.
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
    DraftRecordID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    MediaID,
    NoteID,
    RepositoryID,
    ServiceRecordID,
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
from gda.model.atom.urn import (
    ArchivalURN,
    CemeteryPlotUrn,
    CensusUrn,
    MilitaryDraftUrn,
    SourceURN,
    VitalCertificateUrn,
)

__version__ = "1.0.0+build.12"

__all__ = [
    "AhnentafelNumber",
    "ArchivalURN",
    "AtomID",
    "BirthYear",
    "CemeteryPlotUrn",
    "CensusUrn",
    "CensusYear",
    "CensusYearEnum",
    "ConfidenceScore",
    "Coordinates",
    "DateModifier",
    "DateString",
    "DeathYear",
    "DraftRecordID",
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
    "MilitaryDraftUrn",
    "NewsCategoryCode",
    "NoteID",
    "PubCode",
    "QuayScore",
    "RepositoryID",
    "SiteID",
    "ServiceRecordID",
    "SourceID",
    "SourceURN",
    "TranscriptID",
    "UUIDv4Str",
    "VitalCertificateUrn",
]
