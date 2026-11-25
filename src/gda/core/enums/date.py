"""Path: src/gda/core/enums/date.py

Standardized historical temporal and census enumeration classifications.

Operational Role:
    Defines canonical enumerations for US Federal decennial census schedules
    (CensusYearUS) and genealogical date approximation qualifiers (DateModifier),
    supporting token normalization, GEDCOM date modifier parity, and bounded
    enumeration membership.
"""

from __future__ import annotations

from gda.core.enums.base import GDAIntEnum, GDAStrEnum

__version__ = "1.0.0+build.2"

__all__ = [
    "CensusYearUS",
    "DateModifier",
    "MODIFIER_ALIASES",
    "normalize_modifier",
]


class CensusYearUS(GDAIntEnum):
    """Valid US Federal Decennial Census enumeration years (1790 to 1950)."""

    Y1790 = 1790
    Y1800 = 1800
    Y1810 = 1810
    Y1820 = 1820
    Y1830 = 1830
    Y1840 = 1840
    Y1850 = 1850
    Y1860 = 1860
    Y1870 = 1870
    Y1880 = 1880
    Y1900 = 1900
    Y1910 = 1910
    Y1920 = 1920
    Y1930 = 1930
    Y1940 = 1940
    Y1950 = 1950


class DateModifier(GDAStrEnum):
    """Standardized genealogical date approximations and qualifiers."""

    EXACT = "EXACT"
    ABOUT = "ABT"
    BEFORE = "BEF"
    AFTER = "AFT"
    BETWEEN = "BET"
    ESTIMATED = "EST"
    CALCULATED = "CAL"


MODIFIER_ALIASES: dict[str, DateModifier] = {
    "EXACT": DateModifier.EXACT,
    "ABT": DateModifier.ABOUT,
    "ABOUT": DateModifier.ABOUT,
    "CIRCA": DateModifier.ABOUT,
    "C": DateModifier.ABOUT,
    "CA": DateModifier.ABOUT,
    "BEF": DateModifier.BEFORE,
    "BEFORE": DateModifier.BEFORE,
    "AFT": DateModifier.AFTER,
    "AFTER": DateModifier.AFTER,
    "BET": DateModifier.BETWEEN,
    "BETWEEN": DateModifier.BETWEEN,
    "EST": DateModifier.ESTIMATED,
    "ESTIMATED": DateModifier.ESTIMATED,
    "CAL": DateModifier.CALCULATED,
    "CALCULATED": DateModifier.CALCULATED,
}


def normalize_modifier(modifier: DateModifier | str | None) -> DateModifier | None:
    """Normalize string, enum, or alias into a valid DateModifier instance.

    Args:
        modifier: Raw date modifier string, DateModifier enum member, or None.

    Returns:
        Canonical DateModifier member, or None if input is None.

    Raises:
        ValueError: If modifier cannot be normalized to a recognized DateModifier.
    """
    if modifier is None:
        return None
    if isinstance(modifier, DateModifier):
        return modifier
    token = str(modifier).strip().upper()
    if token in MODIFIER_ALIASES:
        return MODIFIER_ALIASES[token]
    raise ValueError(f"Invalid DateModifier value: '{modifier}'.")
