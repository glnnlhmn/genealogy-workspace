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

__version__ = "1.0.0+build.4"

__all__ = [
    "AffiliationType",
    "ArrivalPassageClass",
    "AssociatedRole",
    "AwardScope",
    "BequestType",
    "BirthPlurality",
    "BountyLandAct",
    "CasualtyCategory",
    "CensusYearUS",
    "CitizenshipStatus",
    "CivilWarConscriptionAllegiance",
    "CivilWarEnrollmentClass",
    "ColonialMilitiaClass",
    "ColonialWarPeriod",
    "DateModifier",
    "DeedPartyRole",
    "DispositionType",
    "DivorceDecreeType",
    "DocumentSide",
    "DraftCardTier",
    "EducationLevel",
    "EstatePropertyCategory",
    "EyeColor",
    "FactType",
    "HairColor",
    "HistoricNameType",
    "HomeOwnership",
    "IDType",
    "IntermentCemeteryType",
    "JurisdictionCategory",
    "LandGrantBasis",
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
    "MembershipStatus",
    "MilitaryAwardTier",
    "MilitaryBranch",
    "MilitaryConflict",
    "MilitaryDraftType",
    "MilitaryWar",
    "ModernDraftEra",
    "MusterRollType",
    "NaturalizationStage",
    "NoteType",
    "OperationalStatus",
    "OrganizationCategory",
    "PedigreeType",
    "PensionClaimantRole",
    "PensionPaymentAuthority",
    "PhysicalBuild",
    "PowCampType",
    "ProbateLedgerEntryKind",
    "PublicationFrequency",
    "QualityAssessment",
    "QuayScore",
    "ResidentialStatus",
    "SelectiveServiceClass",
    "SeparationCharacter",
    "SeparationFormType",
    "ServiceComponent",
    "Sex",
    "SiteType",
    "SmartIDPrefix",
    "SourceRecordCategory",
    "SourceRecordType",
    "SssClassification",
    "TaxpayerClassification",
    "TestimonyMedium",
    "TextQuality",
    "TranscriptLegibility",
    "UnionDissolutionType",
    "UnionType",
    "VitalModifier",
    "WwiCardType",
    "WwiCitizenshipStatus",
    "WwiiDraftWave",
    "normalize_modifier",
]
