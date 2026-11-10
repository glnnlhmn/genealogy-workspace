"""Path: src/gda/core/enums/__init__.py

Authoritative categorical and domain enumerations package for GDA Core.

Operational Role:
    Provides standardized classifications, evidentiary confidence metrics,
    kinship roles, onomastic classifications, temporal qualifiers, and archival categories.
"""

from __future__ import annotations

from gda.core.enums.archival import (
    DocumentSide,
    EyeColor,
    HairColor,
    Legibility,
    NoteType,
    PhysicalBuild,
    PublicationFrequency,
    SelectiveServiceClass,
    TestimonyMedium,
    TextQuality,
    TranscriptLegibility,
    WwiCardType,
)
from gda.core.enums.core import (
    AssociatedRole,
    FactType,
    IDType,
    QualityAssessment,
    QuayScore,
    Sex,
    SmartIDPrefix,
)
from gda.core.enums.date import (
    MODIFIER_ALIASES,
    CensusYearUS,
    DateModifier,
    normalize_modifier,
)
from gda.core.enums.fiscal import (
    CitizenshipStatus,
    HomeOwnership,
    ResidentialStatus,
    TaxpayerClassification,
)
from gda.core.enums.location import (
    JurisdictionCategory,
    LocationType,
)
from gda.core.enums.site import (
    MarkerCondition,
    MarkerMaterial,
    MarkerType,
    OperationalStatus,
    SiteType,
)
from gda.core.enums.sources import (
    EducationLevel,
    MilitaryBranch,
    MilitaryConflict,
    MilitaryDraftType,
    MilitaryWar,
    SourceRecordCategory,
    SourceRecordType,
)
from gda.core.enums.vital import (
    BirthPlurality,
    DispositionType,
    DivorceDecreeType,
    HistoricNameType,
    LegalPlaintiff,
    MannerOfDeath,
    MaritalHistoryDissolution,
    MaritalStatus,
    PedigreeType,
    UnionDissolutionType,
    UnionType,
    VitalModifier,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "AssociatedRole",
    "BirthPlurality",
    "CensusYearUS",
    "CitizenshipStatus",
    "DateModifier",
    "DispositionType",
    "DivorceDecreeType",
    "DocumentSide",
    "EducationLevel",
    "EyeColor",
    "FactType",
    "HairColor",
    "HistoricNameType",
    "HomeOwnership",
    "IDType",
    "JurisdictionCategory",
    "LegalPlaintiff",
    "Legibility",
    "LocationType",
    "MODIFIER_ALIASES",
    "MannerOfDeath",
    "MaritalHistoryDissolution",
    "MaritalStatus",
    "MarkerCondition",
    "MarkerMaterial",
    "MarkerType",
    "MilitaryBranch",
    "MilitaryConflict",
    "MilitaryDraftType",
    "MilitaryWar",
    "NoteType",
    "OperationalStatus",
    "PedigreeType",
    "PhysicalBuild",
    "PublicationFrequency",
    "QualityAssessment",
    "QuayScore",
    "ResidentialStatus",
    "SelectiveServiceClass",
    "Sex",
    "SiteType",
    "SmartIDPrefix",
    "SourceRecordCategory",
    "SourceRecordType",
    "TaxpayerClassification",
    "TestimonyMedium",
    "TextQuality",
    "TranscriptLegibility",
    "UnionDissolutionType",
    "UnionType",
    "VitalModifier",
    "WwiCardType",
    "normalize_modifier",
]
