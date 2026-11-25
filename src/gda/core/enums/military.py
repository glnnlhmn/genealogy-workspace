"""Path: src/gda/core/enums/military.py

Military domain enumerations across service, awards, casualty, pension, and draft records.

Operational Role:
    Provides standardized GDAStrEnum definitions for armed forces branches, service
    components, discharge characterizations, muster roll types, valor award tiers,
    casualty classifications, POW camp categories, cemetery jurisdictions, pension
    claimant roles, bounty land acts, and historical conscription/draft classifications.
"""

from __future__ import annotations

from gda.core.enums.base import GDAStrEnum

__version__ = "1.0.0+build.3"

__all__ = [
    "AwardScope",
    "BountyLandAct",
    "CasualtyCategory",
    "CivilWarConscriptionAllegiance",
    "CivilWarEnrollmentClass",
    "ColonialMilitiaClass",
    "ColonialWarPeriod",
    "DraftCardTier",
    "IntermentCemeteryType",
    "MilitaryAwardTier",
    "MilitaryBranch",
    "MilitaryDraftType",
    "MilitaryWar",
    "ModernDraftEra",
    "MusterRollType",
    "PensionClaimantRole",
    "PensionPaymentAuthority",
    "PowCampType",
    "SeparationCharacter",
    "SeparationFormType",
    "ServiceComponent",
    "SssClassification",
    "WwiCardType",
    "WwiCitizenshipStatus",
    "WwiiDraftWave",
]


# ==============================================================================
# SERVICE & SEPARATION ENUMERATIONS
# ==============================================================================


class MilitaryBranch(GDAStrEnum):
    """Armed force branch designation across historical periods."""

    ARMY = "ARMY"
    NAVY = "NAVY"
    MARINE_CORPS = "MARINE_CORPS"
    AIR_FORCE = "AIR_FORCE"
    COAST_GUARD = "COAST_GUARD"
    CONTINENTAL_ARMY = "CONTINENTAL_ARMY"
    CONTINENTAL_NAVY = "CONTINENTAL_NAVY"
    STATE_MILITIA = "STATE_MILITIA"
    CONFEDERATE_ARMY = "CONFEDERATE_ARMY"
    CONFEDERATE_NAVY = "CONFEDERATE_NAVY"
    MERCHANT_MARINE = "MERCHANT_MARINE"
    OTHER = "OTHER"


class ServiceComponent(GDAStrEnum):
    """Component classification of armed forces service."""

    REGULAR = "REGULAR"
    VOLUNTEER = "VOLUNTEER"
    NATIONAL_GUARD = "NATIONAL_GUARD"
    RESERVE = "RESERVE"
    SELECTIVE_SERVICE_CONSCRIPT = "SELECTIVE_SERVICE_CONSCRIPT"


class SeparationCharacter(GDAStrEnum):
    """Character of discharge or release from military active duty."""

    HONORABLE = "HONORABLE"
    GENERAL_UNDER_HONORABLE = "GENERAL_UNDER_HONORABLE"
    OTHER_THAN_HONORABLE = "OTHER_THAN_HONORABLE"
    BAD_CONDUCT = "BAD_CONDUCT"
    DISHONORABLE = "DISHONORABLE"
    UNCHARACTERIZED = "UNCHARACTERIZED"
    DIED_IN_SERVICE = "DIED_IN_SERVICE"


class MusterRollType(GDAStrEnum):
    """Specific form or administrative type of muster roll."""

    ENLISTMENT_CONTRACT = "ENLISTMENT_CONTRACT"
    MUSTER_IN = "MUSTER_IN"
    BIMONTHLY_MUSTER = "BIMONTHLY_MUSTER"
    MUSTER_OUT = "MUSTER_OUT"
    DESCRIPTIVE_ROLL = "DESCRIPTIVE_ROLL"
    CMSR_JACKET = "CMSR_JACKET"
    SPECIAL_REPRESENTATION = "SPECIAL_REPRESENTATION"


class SeparationFormType(GDAStrEnum):
    """Statutory or administrative certificate form type."""

    DD_214 = "DD_214"
    DD_215 = "DD_215"
    WD_AGO_53_55 = "WD_AGO_53_55"
    NAVPERS_553 = "NAVPERS_553"
    NAVMC_78_PD = "NAVMC_78_PD"
    CERTIFICATE_OF_DISCHARGE = "CERTIFICATE_OF_DISCHARGE"
    OTHER = "OTHER"


class MilitaryWar(GDAStrEnum):
    """Major historical wars and armed conflicts."""

    REVOLUTIONARY = "REVOLUTIONARY"
    WAR_OF_1812 = "WAR_OF_1812"
    CIVIL_WAR = "CIVIL_WAR"
    SPANISH_AMERICAN = "SPANISH_AMERICAN"
    WWI = "WWI"
    WWII = "WWII"
    KOREAN = "KOREAN"
    VIETNAM = "VIETNAM"
    OTHER = "OTHER"


class MilitaryDraftType(GDAStrEnum):
    """Classification of historical military draft and conscription records."""

    DRAFT_REGISTRATION = "DRAFT_REGISTRATION"
    ENROLLMENT_LIST = "ENROLLMENT_LIST"
    CONSCRIPTION_CARD = "CONSCRIPTION_CARD"
    MUSTERING_ROLL = "MUSTERING_ROLL"


# ==============================================================================
# AWARDS & DECORATIONS ENUMERATIONS
# ==============================================================================


class MilitaryAwardTier(GDAStrEnum):
    """Precedence hierarchy and classification of armed forces awards."""

    MEDAL_OF_HONOR = "MEDAL_OF_HONOR"
    DISTINGUISHED_SERVICE_CROSS = "DISTINGUISHED_SERVICE_CROSS"
    NAVY_CROSS = "NAVY_CROSS"
    AIR_FORCE_CROSS = "AIR_FORCE_CROSS"
    SILVER_STAR = "SILVER_STAR"
    DISTINGUISHED_FLYING_CROSS = "DISTINGUISHED_FLYING_CROSS"
    BRONZE_STAR = "BRONZE_STAR"
    PURPLE_HEART = "PURPLE_HEART"
    COMMENDATION_MEDAL = "COMMENDATION_MEDAL"
    ACHIEVEMENT_MEDAL = "ACHIEVEMENT_MEDAL"
    CAMPAIGN_MEDAL = "CAMPAIGN_MEDAL"
    EXPEDITIONARY_MEDAL = "EXPEDITIONARY_MEDAL"
    SERVICE_MEDAL = "SERVICE_MEDAL"
    UNIT_CITATION = "UNIT_CITATION"
    FOREIGN_DECORATION = "FOREIGN_DECORATION"
    OTHER = "OTHER"


class AwardScope(GDAStrEnum):
    """Operational or commemorative scope of military recognition."""

    VALOR_IN_COMBAT = "VALOR_IN_COMBAT"
    MERITORIOUS_SERVICE = "MERITORIOUS_SERVICE"
    WOUND_IN_ACTION = "WOUND_IN_ACTION"
    CAMPAIGN_PARTICIPATION = "CAMPAIGN_PARTICIPATION"
    LONGEVITY_SERVICE = "LONGEVITY_SERVICE"
    MARKSMANSHIP = "MARKSMANSHIP"
    OTHER = "OTHER"


# ==============================================================================
# CASUALTY, POW & BURIAL ENUMERATIONS
# ==============================================================================


class CasualtyCategory(GDAStrEnum):
    """Classification of military casualty event."""

    KILLED_IN_ACTION = "KILLED_IN_ACTION"
    DIED_OF_WOUNDS = "DIED_OF_WOUNDS"
    WOUNDED_IN_ACTION = "WOUNDED_IN_ACTION"
    MISSING_IN_ACTION = "MISSING_IN_ACTION"
    PRISONER_OF_WAR = "PRISONER_OF_WAR"
    DIED_OF_DISEASE = "DIED_OF_DISEASE"
    DIED_IN_SERVICE = "DIED_IN_SERVICE"
    NON_COMBAT_DEATH = "NON_COMBAT_DEATH"
    ACCIDENTAL = "ACCIDENTAL"
    OTHER = "OTHER"


class PowCampType(GDAStrEnum):
    """Prisoner of war camp administrative category."""

    OFFICER_CAMP = "OFFICER_CAMP"
    ENLISTED_CAMP = "ENLISTED_CAMP"
    CIVIL_WAR_STOCKADE = "CIVIL_WAR_STOCKADE"
    INTERNMENT_CENTER = "INTERNMENT_CENTER"
    TEMPORARY_HOLDING = "TEMPORARY_HOLDING"
    OTHER = "OTHER"


class IntermentCemeteryType(GDAStrEnum):
    """Type or jurisdiction of military burial facility."""

    NATIONAL_CEMETERY = "NATIONAL_CEMETERY"
    STATE_VETERANS_CEMETERY = "STATE_VETERANS_CEMETERY"
    ABMC_OVERSEAS = "ABMC_OVERSEAS"
    PRIVATE_CEMETERY = "PRIVATE_CEMETERY"
    POST_CEMETERY = "POST_CEMETERY"
    BATTLEFIELD_BURIAL = "BATTLEFIELD_BURIAL"
    UNKNOWN = "UNKNOWN"


# ==============================================================================
# PENSION & BOUNTY LAND ENUMERATIONS
# ==============================================================================


class PensionClaimantRole(GDAStrEnum):
    """Relationship of the pension claimant to the veteran."""

    VETERAN = "VETERAN"
    WIDOW = "WIDOW"
    REMARRIED_WIDOW = "REMARRIED_WIDOW"
    MINOR_CHILD = "MINOR_CHILD"
    DEPENDENT_PARENT = "DEPENDENT_PARENT"
    OTHER_DEPENDENT = "OTHER_DEPENDENT"


class PensionPaymentAuthority(GDAStrEnum):
    """Statutory or administrative authority governing pension disbursement."""

    US_BUREAU_OF_PENSIONS = "US_BUREAU_OF_PENSIONS"
    US_VETERANS_ADMINISTRATION = "US_VETERANS_ADMINISTRATION"
    CONTINENTAL_CONGRESS = "CONTINENTAL_CONGRESS"
    CONFEDERATE_STATE = "CONFEDERATE_STATE"
    STATE_PENSION_BOARD = "STATE_PENSION_BOARD"
    COLONIAL_ASSEMBLY = "COLONIAL_ASSEMBLY"
    OTHER = "OTHER"


class BountyLandAct(GDAStrEnum):
    """Congressional acts authorizing military bounty land warrant grants."""

    REVOLUTIONARY_WAR_ACTS = "REVOLUTIONARY_WAR_ACTS"
    ACT_OF_1812 = "ACT_OF_1812"
    ACT_OF_1850 = "ACT_OF_1850"
    ACT_OF_1852 = "ACT_OF_1852"
    ACT_OF_1855 = "ACT_OF_1855"
    STATE_MILITARY_DISTRICT = "STATE_MILITARY_DISTRICT"
    OTHER = "OTHER"


# ==============================================================================
# DRAFT, MILITIA & SELECTIVE SERVICE ENUMERATIONS
# ==============================================================================


class DraftCardTier(GDAStrEnum):
    """Controlled classification of US military draft registration rounds."""

    WWI_FIRST = "WWI_FIRST"
    WWI_SECOND = "WWI_SECOND"
    WWI_THIRD = "WWI_THIRD"
    WWII_FOURTH = "WWII_FOURTH"
    OTHER = "OTHER"


class ColonialWarPeriod(GDAStrEnum):
    """Historical conflict or statutory period governing colonial enrollment."""

    COLONIAL_INTERCOLONIAL = "COLONIAL_INTERCOLONIAL"
    FRENCH_AND_INDIAN = "FRENCH_AND_INDIAN"
    REVOLUTIONARY_WAR = "REVOLUTIONARY_WAR"
    EARLY_REPUBLIC = "EARLY_REPUBLIC"


class ColonialMilitiaClass(GDAStrEnum):
    """Statutory readiness or service classification in colonial militia law."""

    TRAINBAND = "TRAINBAND"
    ALARM_LIST = "ALARM_LIST"
    MINUTEMAN = "MINUTEMAN"
    CONTINENTAL_LEVY = "CONTINENTAL_LEVY"
    TOWN_CLASS = "TOWN_CLASS"


class CivilWarConscriptionAllegiance(GDAStrEnum):
    """Allegiance authority governing Civil War draft enrollment."""

    UNION = "UNION"
    CONFEDERATE = "CONFEDERATE"


class CivilWarEnrollmentClass(GDAStrEnum):
    """Statutory enrollment classification under Civil War Conscription/Enrollment Acts."""

    CLASS_1 = "CLASS_1"
    CLASS_2 = "CLASS_2"
    VOLUNTEER_EXEMPT = "VOLUNTEER_EXEMPT"
    CONFEDERATE_GENERAL = "CONFEDERATE_GENERAL"


class WwiCardType(GDAStrEnum):
    """World War I Selective Service registration card formats."""

    CARD_A = "CARD_A"
    CARD_B = "CARD_B"
    CARD_C = "CARD_C"
    UNKNOWN = "UNKNOWN"


class WwiCitizenshipStatus(GDAStrEnum):
    """Controlled classification of citizenship declared on WWI registration cards."""

    NATIVE_BORN = "NATIVE_BORN"
    NATURALIZED_CITIZEN = "NATURALIZED_CITIZEN"
    ALIEN_DECLARED = "ALIEN_DECLARED"
    NON_DECLARANT = "NON_DECLARANT"
    UNKNOWN = "UNKNOWN"


class WwiiDraftWave(GDAStrEnum):
    """Selective Training and Service Act registration waves."""

    FIRST = "FIRST"
    SECOND = "SECOND"
    THIRD = "THIRD"
    FOURTH_OLD_MANS = "FOURTH_OLD_MANS"
    FIFTH = "FIFTH"
    SIXTH = "SIXTH"


class ModernDraftEra(GDAStrEnum):
    """Statutory draft administration era under modern Selective Service."""

    POST_WWII_1948 = "POST_WWII_1948"
    KOREAN_WAR = "KOREAN_WAR"
    VIETNAM_LOTTERY = "VIETNAM_LOTTERY"
    POST_1980_REGISTRATION = "POST_1980_REGISTRATION"


class SssClassification(GDAStrEnum):
    """Selective Service board classification designation."""

    ONE_A = "1-A"
    ONE_A_O = "1-A-O"
    ONE_O = "1-O"
    ONE_D = "1-D"
    TWO_S = "2-S"
    THREE_A = "3-A"
    FOUR_F = "4-F"
    UNCLASSIFIED = "UNCLASSIFIED"
