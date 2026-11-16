"""Path: src/gda/core/enums/__init__.py

Authoritative categorical and domain enumerations package for GDA Core.

Operational Role:
    Provides standardized classifications, evidentiary confidence metrics,
    kinship roles, onomastic classifications, temporal qualifiers, military
    classifications, organization taxonomies, probate/land/immigration
    classifications, and archival categories.
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
from gda.core.enums.immigration import (
    ArrivalPassageClass,
    NaturalizationStage,
)
from gda.core.enums.land import (
    DeedPartyRole,
    LandGrantBasis,
)
from gda.core.enums.location import (
    JurisdictionCategory,
    LocationType,
)
from gda.core.enums.military import (
    AwardScope,
    BountyLandAct,
    CasualtyCategory,
    CivilWarConscriptionAllegiance,
    CivilWarEnrollmentClass,
    ColonialMilitiaClass,
    ColonialWarPeriod,
    DraftCardTier,
    IntermentCemeteryType,
    MilitaryAwardTier,
    MilitaryBranch,
    ModernDraftEra,
    MusterRollType,
    PensionClaimantRole,
    PensionPaymentAuthority,
    PowCampType,
    SeparationCharacter,
    SeparationFormType,
    ServiceComponent,
    SssClassification,
    WwiCitizenshipStatus,
    WwiiDraftWave,
)
from gda.core.enums.orgs import (
    AffiliationType,
    MembershipStatus,
    OrganizationCategory,
)
from gda.core.enums.probate import (
    BequestType,
    EstatePropertyCategory,
    ProbateLedgerEntryKind,
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

__version__ = "1.0.0+build.5"

__all__ = [
    "AffiliationType",  # orgs.py
    "ArrivalPassageClass",  # immigration.py
    "AssociatedRole",  # core.py
    "AwardScope",  # military.py
    "BequestType",  # probate.py
    "BirthPlurality",  # vital.py
    "BountyLandAct",  # military.py
    "CasualtyCategory",  # military.py
    "CensusYearUS",  # date.py
    "CitizenshipStatus",  # fiscal.py
    "CivilWarConscriptionAllegiance",  # military.py
    "CivilWarEnrollmentClass",  # military.py
    "ColonialMilitiaClass",  # military.py
    "ColonialWarPeriod",  # military.py
    "DateModifier",  # date.py
    "DeedPartyRole",  # land.py
    "DispositionType",  # vital.py
    "DivorceDecreeType",  # vital.py
    "DocumentSide",  # archival.py
    "DraftCardTier",  # military.py
    "EducationLevel",  # sources.py
    "EstatePropertyCategory",  # probate.py
    "EyeColor",  # archival.py
    "FactType",  # core.py
    "HairColor",  # archival.py
    "HistoricNameType",  # vital.py
    "HomeOwnership",  # fiscal.py
    "IDType",  # core.py
    "IntermentCemeteryType",  # military.py
    "JurisdictionCategory",  # location.py
    "LandGrantBasis",  # land.py
    "LegalPlaintiff",  # vital.py
    "Legibility",  # archival.py
    "LocationType",  # location.py
    "MODIFIER_ALIASES",  # date.py
    "MannerOfDeath",  # vital.py
    "MaritalHistoryDissolution",  # vital.py
    "MaritalStatus",  # vital.py
    "MarkerCondition",  # site.py
    "MarkerMaterial",  # site.py
    "MarkerType",  # site.py
    "MembershipStatus",  # orgs.py
    "MilitaryAwardTier",  # military.py
    "MilitaryBranch",  # military.py
    "MilitaryConflict",  # sources.py
    "MilitaryDraftType",  # sources.py
    "MilitaryWar",  # sources.py
    "ModernDraftEra",  # military.py
    "MusterRollType",  # military.py
    "NaturalizationStage",  # immigration.py
    "NoteType",  # archival.py
    "OperationalStatus",  # site.py
    "OrganizationCategory",  # orgs.py
    "PedigreeType",  # vital.py
    "PensionClaimantRole",  # military.py
    "PensionPaymentAuthority",  # military.py
    "PhysicalBuild",  # archival.py
    "PowCampType",  # military.py
    "ProbateLedgerEntryKind",  # probate.py
    "PublicationFrequency",  # archival.py
    "QualityAssessment",  # core.py
    "QuayScore",  # core.py
    "ResidentialStatus",  # fiscal.py
    "SelectiveServiceClass",  # archival.py
    "SeparationCharacter",  # military.py
    "SeparationFormType",  # military.py
    "ServiceComponent",  # military.py
    "Sex",  # core.py
    "SiteType",  # site.py
    "SmartIDPrefix",  # core.py
    "SourceRecordCategory",  # sources.py
    "SourceRecordType",  # sources.py
    "SssClassification",  # military.py
    "TaxpayerClassification",  # fiscal.py
    "TestimonyMedium",  # archival.py
    "TextQuality",  # archival.py
    "TranscriptLegibility",  # archival.py
    "UnionDissolutionType",  # vital.py
    "UnionType",  # vital.py
    "VitalModifier",  # vital.py
    "WwiCardType",  # archival.py
    "WwiCitizenshipStatus",  # military.py
    "WwiiDraftWave",  # military.py
    "normalize_modifier",  # date.py
]
