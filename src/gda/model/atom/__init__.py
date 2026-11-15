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
    OrganizationID,
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

__version__ = "1.0.0+build.3"

__all__ = [
    "AhnentafelNumber",  # scalar.py
    "ArchivalURN",  # urn.py
    "AtomID",  # id.py
    "BirthYear",  # year.py
    "CemeteryPlotUrn",  # urn.py
    "CensusUrn",  # urn.py
    "ConfidenceScore",  # scalar.py
    "DateString",  # date.py
    "DeathYear",  # year.py
    "DraftRecordID",  # id.py
    "FactID",  # id.py
    "FamilyID",  # id.py
    "GenderAtom",  # gender.py
    "HistoricalYear",  # year.py
    "IndividualID",  # id.py
    "IsoTimestamp",  # date.py
    "Latitude",  # geo.py
    "LocationID",  # id.py
    "Longitude",  # geo.py
    "MediaID",  # id.py
    "MilitaryDraftUrn",  # urn.py
    "NewsCategoryCode",  # scalar.py
    "NoteID",  # id.py
    "OrganizationID",  # id.py
    "PubCode",  # scalar.py
    "QuayScore",  # scalar.py
    "RepositoryID",  # id.py
    "ServiceRecordID",  # id.py
    "SiteID",  # id.py
    "SourceID",  # id.py
    "SourceURN",  # urn.py
    "TranscriptID",  # id.py
    "UUIDv4Str",  # id.py
    "VitalCertificateUrn",  # urn.py
]
