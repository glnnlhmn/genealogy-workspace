"""Path: src/gda/core/enums/__init__.py

Authoritative categorical and domain enumerations package for GDA Core.

Operational Role:
    Provides standardized classifications, evidentiary confidence metrics,
    kinship roles, onomastic classifications, temporal qualifiers, military
    classifications, organization taxonomies, probate/land/immigration
    classifications, archival categories, and enum base/coercion primitives.
"""

from __future__ import annotations

from gda.core.enums.archival import (
    DocumentSide,
    Legibility,
    NoteType,
    PublicationFrequency,
    TestimonyMedium,
    TextQuality,
)
from gda.core.enums.base import (
    GDAIntEnum,
    GDAStrEnum,
    coerce_enum,
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
    MilitaryDraftType,
    MilitaryWar,
    ModernDraftEra,
    MusterRollType,
    PensionClaimantRole,
    PensionPaymentAuthority,
    PowCampType,
    SeparationCharacter,
    SeparationFormType,
    ServiceComponent,
    SssClassification,
    WwiCardType,
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
    SourceRecordCategory,
    SourceRecordType,
)
from gda.core.enums.vital import (
    BirthPlurality,
    DispositionType,
    DivorceDecreeType,
    EducationLevel,
    EyeColor,
    HairColor,
    HistoricNameType,
    LegalPlaintiff,
    MannerOfDeath,
    MaritalStatus,
    PedigreeType,
    PhysicalBuild,
    UnionDissolutionType,
    UnionType,
    VitalModifier,
)

__version__ = "1.0.0+build.10"

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
    "EducationLevel",  # vital.py
    "EstatePropertyCategory",  # probate.py
    "EyeColor",  # vital.py
    "FactType",  # core.py
    "GDAIntEnum",  # base.py
    "GDAStrEnum",  # base.py
    "HairColor",  # vital.py
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
    "MaritalStatus",  # vital.py
    "MarkerCondition",  # site.py
    "MarkerMaterial",  # site.py
    "MarkerType",  # site.py
    "MembershipStatus",  # orgs.py
    "MilitaryAwardTier",  # military.py
    "MilitaryBranch",  # military.py
    "MilitaryDraftType",  # military.py
    "MilitaryWar",  # military.py
    "ModernDraftEra",  # military.py
    "MusterRollType",  # military.py
    "NaturalizationStage",  # immigration.py
    "NoteType",  # archival.py
    "OperationalStatus",  # site.py
    "OrganizationCategory",  # orgs.py
    "PedigreeType",  # vital.py
    "PensionClaimantRole",  # military.py
    "PensionPaymentAuthority",  # military.py
    "PhysicalBuild",  # vital.py
    "PowCampType",  # military.py
    "ProbateLedgerEntryKind",  # probate.py
    "PublicationFrequency",  # archival.py
    "QualityAssessment",  # core.py
    "QuayScore",  # core.py
    "ResidentialStatus",  # fiscal.py
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
    "UnionDissolutionType",  # vital.py
    "UnionType",  # vital.py
    "VitalModifier",  # vital.py
    "WwiCardType",  # military.py
    "WwiCitizenshipStatus",  # military.py
    "WwiiDraftWave",  # military.py
    "coerce_enum",  # base.py
    "normalize_modifier",  # date.py
]
