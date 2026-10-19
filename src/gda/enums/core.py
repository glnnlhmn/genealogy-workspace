"""Path: src/gda/enums/core.py

Foundational domain classifications, assessment metrics, and certainty scores.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum

__version__ = "0.2.0+build.5"

__all__ = [
    "AssociatedRole",
    "DateModifier",
    "FactType",
    "QualityAssessment",
    "QuayScore",
    "Sex",
    "VitalModifier",
]


class Sex(StrEnum):
    """Biological or recorded sex classification on historical records."""

    M = "M"
    MALE = "M"
    F = "F"
    FEMALE = "F"
    X = "X"
    NON_BINARY = "X"
    U = "U"
    UNKNOWN = "U"

    @classmethod
    def from_input(cls, val: str) -> Sex:
        """Map raw transcription tokens or full strings to canonical Sex codes."""
        token = val.strip().upper()
        mapping = {
            "M": cls.M,
            "MALE": cls.MALE,
            "BOY": cls.MALE,
            "F": cls.FEMALE,
            "FEMALE": cls.FEMALE,
            "GIRL": cls.FEMALE,
            "X": cls.NON_BINARY,
            "NON-BINARY": cls.NON_BINARY,
            "U": cls.UNKNOWN,
            "UNDETERMINED": cls.UNKNOWN,
            "UNKNOWN": cls.UNKNOWN,
        }
        if token in mapping:
            return mapping[token]
        raise ValueError(f"Cannot map '{val}' to a valid Sex enum member.")


class FactType(StrEnum):
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


class AssociatedRole(StrEnum):
    """Standardized participant roles for associated individuals."""

    # Primary Kinship
    PRIMARY = "PRIMARY"
    CHIL = "CHIL"
    CHILD = "CHIL"
    HUSB = "HUSB"
    HUSBAND = "HUSB"
    WIFE = "WIFE"
    MOTH = "MOTH"
    MOTHER = "MOTH"
    FATH = "FATH"
    FATHER = "FATH"
    SPOU = "SPOU"
    SPOUSE = "SPOU"
    SIBL = "SIBL"
    SIBLING = "SIBL"

    # Attestation & Legal
    WITN = "WITN"
    WITNESS = "WITN"
    GODP = "GODP"
    GODPARENT = "GODP"
    INFORMANT = "INFORMANT"
    CLERGY = "CLERGY"
    OFFICIANT = "OFFICIANT"
    OFFICIAL = "OFFICIANT"
    NEIGHBOR = "NEIGHBOR"
    ATND = "ATND"
    ATTENDANT = "ATND"
    UNDR = "UNDR"
    UNDERTAKER = "UNDR"
    PHYSICIAN = "PHYSICIAN"
    BONDSMAN = "BONDSMAN"
    ATTORNEY = "ATTORNEY"
    EMPLOYER = "EMPLOYER"
    SPONSOR = "SPONSOR"
    DEC = "DEC"
    DECEASED = "DEC"
    OTHR = "OTHR"
    OTHER = "OTHR"
    UNKNOWN = "UNKNOWN"


class DateModifier(StrEnum):
    """Temporal modifiers qualifying event date precision."""

    EXACT = "EXACT"
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    ABOUT = "ABOUT"
    BETWEEN = "BETWEEN"
    FROM = "FROM"
    TO = "TO"
    ESTIMATED = "ESTIMATED"
    CALCULATED = "CALCULATED"


class VitalModifier(StrEnum):
    """Vital condition modifiers for birth and infant death assertions."""

    STILLBORN = "STILLBORN"
    INFANT = "INFANT"
    ILLEGITIMATE = "ILLEGITIMATE"
    POSTHUMOUS = "POSTHUMOUS"
    LEGITIMATED = "LEGITIMATED"


class QuayScore(IntEnum):
    """Standardized genealogical evidence certainty score (0-3)."""

    UNRELIABLE = 0
    QUESTIONABLE = 1
    SECONDARY = 2
    DIRECT_PRIMARY = 3
    DIRECT = 3
    PRIMARY = 3


class QualityAssessment(StrEnum):
    """Archival evidence certainty textual ratings."""

    DIRECT_PRIMARY = "DIRECT_PRIMARY"
    INDIRECT_PRIMARY = "INDIRECT_PRIMARY"
    SECONDARY = "SECONDARY"
    UNRELIABLE = "UNRELIABLE"
