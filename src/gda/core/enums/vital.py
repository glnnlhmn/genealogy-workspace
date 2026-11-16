"""Path: src/gda/core/enums/vital.py

Demographic statuses, vital event assertions, and domestic relations enums.

Operational Role:
    Defines controlled vocabularies for vital life events, domestic unions,
    marital dissolutions, pedigree linkages, and mortuary disposition types.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.0.0+build.1"

__all__ = [
    "BirthPlurality",
    "DispositionType",
    "DivorceDecreeType",
    "HistoricNameType",
    "LegalPlaintiff",
    "MannerOfDeath",
    "MaritalHistoryDissolution",
    "MaritalStatus",
    "PedigreeType",
    "UnionDissolutionType",
    "UnionType",
    "VitalModifier",
]


class UnionType(StrEnum):
    """Classification of union or domestic partnership inception."""

    MARRIED = "MARRIED"
    COMMON_LAW = "COMMON_LAW"
    CIVIL_UNION = "CIVIL_UNION"
    INFORMAL = "INFORMAL"
    UNKNOWN = "UNKNOWN"


class UnionDissolutionType(StrEnum):
    """Classification of union dissolution, separation, or termination."""

    DIVORCE = "DIVORCE"
    ANNULMENT = "ANNULMENT"
    SEPARATION = "SEPARATION"
    DEATH = "DEATH"
    DESERTION = "DESERTION"
    UNKNOWN = "UNKNOWN"


class PedigreeType(StrEnum):
    """Lineage pedigree classification connecting a child to a family unit."""

    BIRTH = "Birth"
    ADOPTED = "Adopted"
    STEP = "Step"
    FOSTER = "Foster"
    UNKNOWN = "Unknown"


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


class HistoricNameType(StrEnum):
    """Functional classification of historical naming variants and cultural contexts."""

    PRIMARY = "PRIMARY"
    HISTORICAL = "HISTORICAL"
    COLLOQUIAL = "COLLOQUIAL"
    COLONIAL = "COLONIAL"
    INDIGENOUS = "INDIGENOUS"


class VitalModifier(StrEnum):
    """Vital condition modifiers for birth and infant death assertions."""

    STILLBORN = "STILLBORN"
    INFANT = "INFANT"
    ILLEGITIMATE = "ILLEGITIMATE"
    POSTHUMOUS = "POSTHUMOUS"
    LEGITIMATED = "LEGITIMATED"
