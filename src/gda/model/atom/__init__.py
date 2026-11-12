"""Path: src/gda/model/atom/__init__.py

Atomic identification, temporal, metric, and spatial primitives package.

Operational Role:
    Exposes immutable foundational atoms representing identifiers, calendar dates,
    geospatial coordinates, scalar values, and archival URN references.
"""

from __future__ import annotations

from gda.model.atom.date import (
    DateString,
    IsoTimestamp,
)
from gda.model.atom.gender import (
    GenderAtom,
)
from gda.model.atom.geo import (
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
from gda.model.atom.year import (
    BirthYear,
    DeathYear,
    HistoricalYear,
)

__version__ = "1.0.2+build.2"

__all__ = [
    "AhnentafelNumber",  # gda.model.atom.scalar
    "ArchivalURN",  # gda.model.atom.urn
    "AtomID",  # gda.model.atom.id
    "BirthYear",  # gda.model.atom.year
    "CemeteryPlotUrn",  # gda.model.atom.urn
    "CensusUrn",  # gda.model.atom.urn
    "ConfidenceScore",  # gda.model.atom.scalar
    "DateString",  # gda.model.atom.date
    "DeathYear",  # gda.model.atom.year
    "DraftRecordID",  # gda.model.atom.id
    "FactID",  # gda.model.atom.id
    "FamilyID",  # gda.model.atom.id
    "GenderAtom",  # gda.model.atom.gender
    "HistoricalYear",  # gda.model.atom.year
    "IndividualID",  # gda.model.atom.id
    "IsoTimestamp",  # gda.model.atom.date
    "Latitude",  # gda.model.atom.geo
    "LocationID",  # gda.model.atom.id
    "Longitude",  # gda.model.atom.geo
    "MediaID",  # gda.model.atom.id
    "MilitaryDraftUrn",  # gda.model.atom.urn
    "NewsCategoryCode",  # gda.model.atom.scalar
    "NoteID",  # gda.model.atom.id
    "PubCode",  # gda.model.atom.scalar
    "QuayScore",  # gda.model.atom.scalar
    "RepositoryID",  # gda.model.atom.id
    "ServiceRecordID",  # gda.model.atom.id
    "SiteID",  # gda.model.atom.id
    "SourceID",  # gda.model.atom.id
    "SourceURN",  # gda.model.atom.urn
    "TranscriptID",  # gda.model.atom.id
    "UUIDv4Str",  # gda.model.atom.id
    "VitalCertificateUrn",  # gda.model.atom.urn
]
