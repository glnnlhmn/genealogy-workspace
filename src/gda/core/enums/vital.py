"""Path: src/gda/core/enums/vital.py

Demographic statuses, vital event assertions, biographical traits, and domestic relations enums.

Operational Role:
    Defines controlled vocabularies for vital life events, domestic unions,
    marital dissolutions, pedigree linkages, mortuary disposition types,
    educational attainment, and physical trait classifications.
"""

from __future__ import annotations

from gda.core.enums.base import GDAStrEnum

__version__ = "1.0.0+build.3"

__all__ = [
    "BirthPlurality",
    "DispositionType",
    "DivorceDecreeType",
    "EducationLevel",
    "EyeColor",
    "HairColor",
    "HistoricNameType",
    "LegalPlaintiff",
    "MannerOfDeath",
    "MaritalStatus",
    "PedigreeType",
    "PhysicalBuild",
    "UnionDissolutionType",
    "UnionType",
    "VitalModifier",
]


class UnionType(GDAStrEnum):
    """Classification of union or domestic partnership inception."""

    MARRIED = "MARRIED"
    COMMON_LAW = "COMMON_LAW"
    CIVIL_UNION = "CIVIL_UNION"
    INFORMAL = "INFORMAL"
    UNKNOWN = "UNKNOWN"


class UnionDissolutionType(GDAStrEnum):
    """Classification of union dissolution, separation, or termination."""

    DIVORCE = "DIVORCE"
    ANNULMENT = "ANNULMENT"
    SEPARATION = "SEPARATION"
    DEATH = "DEATH"
    DESERTION = "DESERTION"
    UNKNOWN = "UNKNOWN"


class PedigreeType(GDAStrEnum):
    """Lineage pedigree classification connecting a child to a family unit."""

    BIRTH = "BIRTH"
    ADOPTED = "ADOPTED"
    STEP = "STEP"
    FOSTER = "FOSTER"
    UNKNOWN = "UNKNOWN"


class MaritalStatus(GDAStrEnum):
    """Marital status recorded on historical schedules and vital certificates."""

    SINGLE = "SINGLE"
    MARRIED = "MARRIED"
    WIDOWED = "WIDOWED"
    DIVORCED = "DIVORCED"
    UNKNOWN = "UNKNOWN"


class MannerOfDeath(GDAStrEnum):
    """Categorical manner of death classification."""

    NATURAL = "NATURAL"
    ACCIDENT = "ACCIDENT"
    SUICIDE = "SUICIDE"
    HOMICIDE = "HOMICIDE"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"


class BirthPlurality(GDAStrEnum):
    """Birth plurality recorded on vital birth registers."""

    SINGLE = "SINGLE"
    TWIN = "TWIN"
    TRIPLET = "TRIPLET"
    QUADRUPLET = "QUADRUPLET"


class DispositionType(GDAStrEnum):
    """Manner of mortal disposition on death certificates."""

    BURIAL = "BURIAL"
    CREMATION = "CREMATION"
    REMOVAL = "REMOVAL"
    ENTOMBMENT = "ENTOMBMENT"
    DONATION = "DONATION"
    OTHER = "OTHER"


class DivorceDecreeType(GDAStrEnum):
    """Legal classifications for divorce and dissolution decrees."""

    ABSOLUTE = "ABSOLUTE"
    BED_AND_BOARD = "BED_AND_BOARD"
    ANNULMENT = "ANNULMENT"
    DISMISSED = "DISMISSED"
    OTHER = "OTHER"


class LegalPlaintiff(GDAStrEnum):
    """Designation of plaintiff party in civil proceedings."""

    HUSBAND = "HUSBAND"
    WIFE = "WIFE"
    OTHER = "OTHER"


class HistoricNameType(GDAStrEnum):
    """Functional classification of historical naming variants and cultural contexts."""

    PRIMARY = "PRIMARY"
    HISTORICAL = "HISTORICAL"
    COLLOQUIAL = "COLLOQUIAL"
    COLONIAL = "COLONIAL"
    INDIGENOUS = "INDIGENOUS"


class VitalModifier(GDAStrEnum):
    """Vital condition modifiers for birth and infant death assertions."""

    STILLBORN = "STILLBORN"
    INFANT = "INFANT"
    ILLEGITIMATE = "ILLEGITIMATE"
    POSTHUMOUS = "POSTHUMOUS"
    LEGITIMATED = "LEGITIMATED"


class PhysicalBuild(GDAStrEnum):
    """Physical build classifications extracted from historical draft records."""

    SLENDER = "SLENDER"
    MEDIUM = "MEDIUM"
    STOUT = "STOUT"


class EyeColor(GDAStrEnum):
    """Eye color categories extracted from historical draft or identification cards."""

    BLUE = "BLUE"
    BROWN = "BROWN"
    GREY = "GREY"
    HAZEL = "HAZEL"
    BLACK = "BLACK"
    GREEN = "GREEN"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class HairColor(GDAStrEnum):
    """Hair color categories extracted from historical draft or identification cards."""

    BLONDE = "BLONDE"
    BROWN = "BROWN"
    BLACK = "BLACK"
    RED = "RED"
    GREY = "GREY"
    BALD = "BALD"
    WHITE = "WHITE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class EducationLevel(GDAStrEnum):
    """Standard educational attainment tokens."""

    ELEM = "ELEM"
    HS = "HS"
    COLL = "COLL"
    GRAD = "GRAD"
    VOC = "VOC"
    OTHER = "OTHER"
