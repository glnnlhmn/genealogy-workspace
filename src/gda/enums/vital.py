# Name: vital.py
# Path: src/gda/enums/vital.py

"""Demographic statuses, vital event assertions, and domestic relations enums."""

from __future__ import annotations

from enum import StrEnum

__version__ = "0.1.0+build.r1"

__all__ = [
    "BirthPlurality",
    "DispositionType",
    "DivorceDecreeType",
    "LegalPlaintiff",
    "MannerOfDeath",
    "MaritalHistoryDissolution",
    "MaritalStatus",
    "UnionStatus",
]


class UnionStatus(StrEnum):
    """Legal, domestic, or biological partnership status."""

    MARRIED = "MARRIED"
    DIVORCED = "DIVORCED"
    ANNULLED = "ANNULLED"
    SEPARATED = "SEPARATED"
    COMMON_LAW = "COMMON_LAW"
    WIDOWED = "WIDOWED"
    PARTNER = "PARTNER"
    UNKNOWN = "UNKNOWN"


class MaritalStatus(StrEnum):
    """Marital status recorded on historical schedules and vital certificates."""

    SINGLE = "Single"
    MARRIED = "Married"
    WIDOWED = "Widowed"
    DIVORCED = "Divorced"
    UNKNOWN = "Unknown"


class MannerOfDeath(StrEnum):
    """Categorical manner of death classification."""

    NATURAL = "Natural"
    ACCIDENT = "Accident"
    SUICIDE = "Suicide"
    HOMICIDE = "Homicide"
    PENDING = "Pending"
    UNKNOWN = "Unknown"


class BirthPlurality(StrEnum):
    """Birth plurality recorded on vital birth registers."""

    SINGLE = "Single"
    TWIN = "Twin"
    TRIPLET = "Triplet"
    QUADRUPLET = "Quadruplet"


class DispositionType(StrEnum):
    """Manner of mortal disposition on death certificates."""

    BURIAL = "Burial"
    CREMATION = "Cremation"
    REMOVAL = "Removal"
    ENTOMBMENT = "Entombment"
    DONATION = "Donation"
    OTHER = "Other"


class DivorceDecreeType(StrEnum):
    """Legal classifications for divorce and dissolution decrees."""

    ABSOLUTE = "Absolute (A Vinculo Matrimonii)"
    BED_AND_BOARD = "Bed and Board (A Mensa Et Thoro)"
    ANNULMENT = "Annulment"
    DISMISSED = "Dismissed"
    OTHER = "Other"


class LegalPlaintiff(StrEnum):
    """Designation of plaintiff party in civil proceedings."""

    HUSBAND = "Husband"
    WIFE = "Wife"
    OTHER = "Other"


class MaritalHistoryDissolution(StrEnum):
    """Prior marriage dissolution grounds reported on marriage applications."""

    DEATH = "Death"
    DIVORCE = "Divorce"
    ANNULMENT = "Annulment"
    NONE = "None"
