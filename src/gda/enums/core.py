# Name: core.py
# Path: src/gda/enums/core.py

"""Core taxonomic enums, evidentiary ratings, and temporal precision modifiers."""

from __future__ import annotations

from enum import IntEnum, StrEnum

__version__ = "0.1.0+build.r1"

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
    """Biological sex classification matching schema tokens."""

    M = "M"
    F = "F"
    U = "U"


class QuayScore(IntEnum):
    """Standardized genealogical evidence certainty score (0-3)."""

    UNRELIABLE = 0
    QUESTIONABLE = 1
    SECONDARY = 2
    DIRECT_PRIMARY = 3


class QualityAssessment(StrEnum):
    """Archival evidence certainty textual ratings."""

    DIRECT_PRIMARY = "DIRECT_PRIMARY"
    INDIRECT_PRIMARY = "INDIRECT_PRIMARY"
    SECONDARY = "SECONDARY"
    QUESTIONABLE = "QUESTIONABLE"
    UNRELIABLE = "UNRELIABLE"


class FactType(StrEnum):
    """Standardized historical fact assertion categories."""

    ASSOCIATION = "Association"
    AWARD = "Award"
    BAPTISM = "Baptism"
    BIRTH = "Birth"
    BURIAL = "Burial"
    CENSUS = "Census"
    CIVIC = "Civic"
    DEATH = "Death"
    DIVORCE = "Divorce"
    EDUCATION = "Education"
    INCIDENT = "Incident"
    LEGAL = "Legal"
    MARRIAGE = "Marriage"
    MILITARY = "Military"
    OCCUPATION = "Occupation"
    PARENTAGE = "Parentage"
    PROBATE = "Probate"
    PROPERTY = "Property"
    RESIDENCE = "Residence"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class AssociatedRole(StrEnum):
    """Standardized kinship, clerical, or legal participant roles."""

    CHIL = "CHIL"
    HUSB = "HUSB"
    WIFE = "WIFE"
    MOTH = "MOTH"
    FATH = "FATH"
    SPOU = "SPOU"
    SIBL = "SIBL"
    WITN = "WITN"
    GODP = "GODP"
    INFORMANT = "INFORMANT"
    CLERGY = "CLERGY"
    OFFICIANT = "OFFICIANT"
    NEIGHBOR = "NEIGHBOR"
    ATND = "ATND"
    UNDR = "UNDR"
    DEC = "DEC"
    OTHR = "OTHR"
    UNKNOWN = "UNKNOWN"


class DateModifier(StrEnum):
    """Precision and boundary modifiers for historical dates."""

    EXACT = "EXACT"
    ABT = "ABT"
    BEF = "BEF"
    AFT = "AFT"
    BET = "BET"
    FROM_TO = "FROM_TO"
    UNKNOWN = "UNKNOWN"


class VitalModifier(StrEnum):
    """Vital status certainty and boundary modifiers."""

    EXACT = "EXACT"
    ABT = "ABT"
    BEF = "BEF"
    AFT = "AFT"
    BET = "BET"
    FROM_TO = "FROM_TO"
    LIVING = "LIVING"
    UNKNOWN = "UNKNOWN"
