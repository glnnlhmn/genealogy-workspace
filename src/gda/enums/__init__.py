"""Path: src/gda/enums/__init__.py

Authoritative controlled enumerations across the digital archive framework.
"""

from __future__ import annotations

from gda.enums.archival import (
    DocumentSide,
    EyeColor,
    HairColor,
    NoteCategory,
    NoteType,
    PhysicalBuild,
    PublicationFrequency,
    SelectiveServiceClass,
    TestimonyMedium,
    TranscriptLegibility,
    WwiCardType,
)
from gda.enums.core import (
    AssociatedRole,
    DateModifier,
    FactType,
    QualityAssessment,
    QuayScore,
    Sex,
    VitalModifier,
)
from gda.enums.fiscal import (
    CitizenshipStatus,
    HomeOwnership,
    ResidentialStatus,
    TaxpayerClassification,
)
from gda.enums.site import (
    LocationType,
    MarkerCondition,
    MarkerMaterial,
    MarkerType,
    OperationalStatus,
    SiteType,
)
from gda.enums.sources import (
    CensusYear,
    EducationLevel,
    MilitaryBranch,
    MilitaryConflict,
    MilitaryDraftType,
    MilitaryWar,
    SourceRecordCategory,
    SourceRecordType,
)
from gda.enums.vital import (
    BirthPlurality,
    DispositionType,
    DivorceDecreeType,
    LegalPlaintiff,
    MannerOfDeath,
    MaritalHistoryDissolution,
    MaritalStatus,
    NameStatus,
    PedigreeType,
    UnionDissolutionType,
    UnionType,
)

__version__ = "0.1.0+build.r2"

__all__ = [
    # Archival
    "DocumentSide",
    "NoteCategory",
    "NoteType",
    "PublicationFrequency",
    "SelectiveServiceClass",
    "TestimonyMedium",
    "TranscriptLegibility",
    "WwiCardType",
    "PhysicalBuild",
    "EyeColor",
    "HairColor",
    # Core
    "AssociatedRole",
    "DateModifier",
    "FactType",
    "QualityAssessment",
    "QuayScore",
    "Sex",
    "VitalModifier",
    # Fiscal
    "CitizenshipStatus",
    "HomeOwnership",
    "ResidentialStatus",
    "TaxpayerClassification",
    # Site
    "LocationType",
    "MarkerCondition",
    "MarkerMaterial",
    "MarkerType",
    "OperationalStatus",
    "SiteType",
    # Sources
    "CensusYear",
    "EducationLevel",
    "MilitaryBranch",
    "MilitaryConflict",
    "MilitaryDraftType",
    "MilitaryWar",
    "SourceRecordCategory",
    "SourceRecordType",
    # Vital
    "BirthPlurality",
    "DispositionType",
    "DivorceDecreeType",
    "LegalPlaintiff",
    "MannerOfDeath",
    "MaritalHistoryDissolution",
    "MaritalStatus",
    "PedigreeType",
    "UnionDissolutionType",
    "UnionType",
    "NameStatus",
]
