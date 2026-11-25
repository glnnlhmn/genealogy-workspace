"""Path: src/gda/core/enums/core.py

Foundational domain classifications, assessment metrics, and certainty scores.

Operational Role:
    Defines core enumerations for participant roles, entity fact types,
    identifier types, evidence certainty metrics, biological sex, and smartID prefixes.
"""

from __future__ import annotations

from gda.core.enums.base import GDAIntEnum, GDAStrEnum

__version__ = "1.0.0+build.4"

__all__ = [
    "AssociatedRole",
    "FactType",
    "IDType",
    "QualityAssessment",
    "QuayScore",
    "Sex",
    "SmartIDPrefix",
]


class IDType(GDAStrEnum):
    """Authoritative identifier format categories."""

    SMART_ID = "SMART_ID"
    UUID = "UUID"


class Sex(GDAStrEnum):
    """Biological or recorded sex classification on historical records."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_input(cls, val: str) -> Sex:
        """Map raw transcription tokens or full strings to canonical Sex members."""
        token = val.strip().upper()
        mapping = {
            "M": cls.MALE,
            "MALE": cls.MALE,
            "BOY": cls.MALE,
            "F": cls.FEMALE,
            "FEMALE": cls.FEMALE,
            "GIRL": cls.FEMALE,
            "U": cls.UNKNOWN,
            "UNDETERMINED": cls.UNKNOWN,
            "UNKNOWN": cls.UNKNOWN,
        }
        if token in mapping:
            return mapping[token]
        raise ValueError(f"Cannot map '{val}' to a valid Sex enum member.")


class FactType(GDAStrEnum):
    """Authoritative event classification for life assertions."""

    ASSOCIATION = "ASSOCIATION"
    AWARD = "AWARD"
    BAPTISM = "BAPTISM"
    BIRTH = "BIRTH"
    BURIAL = "BURIAL"
    CENSUS = "CENSUS"
    CIVIC = "CIVIC"
    DEATH = "DEATH"
    DIVORCE = "DIVORCE"
    EDUCATION = "EDUCATION"
    IMMIGRATION = "IMMIGRATION"
    INCIDENT = "INCIDENT"
    LAND_RECORD = "LAND_RECORD"
    LEGAL = "LEGAL"
    MARRIAGE = "MARRIAGE"
    MILITARY = "MILITARY"
    NATURALIZATION = "NATURALIZATION"
    OCCUPATION = "OCCUPATION"
    PARENTAGE = "PARENTAGE"
    PROBATE = "PROBATE"
    PROPERTY = "PROPERTY"
    RELIGION = "RELIGION"
    RESIDENCE = "RESIDENCE"
    RETIREMENT = "RETIREMENT"
    TAX = "TAX"
    TRAVEL = "TRAVEL"
    WILL = "WILL"
    OTHER = "OTHER"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"


class AssociatedRole(GDAStrEnum):
    """Standardized participant roles for associated individuals."""

    # Primary Kinship
    PRIMARY = "PRIMARY"
    CHILD = "CHILD"
    HUSBAND = "HUSBAND"
    WIFE = "WIFE"
    MOTHER = "MOTHER"
    FATHER = "FATHER"
    SPOUSE = "SPOUSE"
    SIBLING = "SIBLING"

    # Attestation & Legal
    ATTENDANT = "ATTENDANT"
    ATTORNEY = "ATTORNEY"
    BONDSMAN = "BONDSMAN"
    CLERGY = "CLERGY"
    DECEASED = "DECEASED"
    EMPLOYER = "EMPLOYER"
    FAMILY = "FAMILY"
    GODPARENT = "GODPARENT"
    INFORMANT = "INFORMANT"
    NEIGHBOR = "NEIGHBOR"
    NEXT_OF_KIN = "NEXT_OF_KIN"
    OFFICIAL = "OFFICIAL"
    OFFICIANT = "OFFICIANT"
    OTHER = "OTHER"
    PHYSICIAN = "PHYSICIAN"
    REGISTRAR = "REGISTRAR"
    SPONSOR = "SPONSOR"
    UNDERTAKER = "UNDERTAKER"
    UNKNOWN = "UNKNOWN"
    WITNESS = "WITNESS"


class SmartIDPrefix(GDAStrEnum):
    """Canonical 3-letter prefix classifications for smart entity identifiers."""

    IND = "IND"  # Individual
    FID = "FID"  # Fact
    LOC = "LOC"  # Location
    SID = "SID"  # Site
    FAM = "FAM"  # Family
    NOT = "NOT"  # Note
    REP = "REP"  # Repository
    DRF = "DRF"  # DraftRecord
    ORG = "ORG"  # Organization


class QuayScore(GDAIntEnum):
    """Standardized genealogical evidence certainty score (0-3)."""

    UNRELIABLE = 0
    QUESTIONABLE = 1
    SECONDARY = 2
    DIRECT_PRIMARY = 3


class QualityAssessment(GDAStrEnum):
    """Archival evidence certainty textual ratings."""

    DIRECT_PRIMARY = "DIRECT_PRIMARY"
    INDIRECT_PRIMARY = "INDIRECT_PRIMARY"
    SECONDARY = "SECONDARY"
    UNRELIABLE = "UNRELIABLE"
