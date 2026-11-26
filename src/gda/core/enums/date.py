"""Path: src/gda/core/enums/date.py

Standardized historical temporal and census enumeration classifications.

Operational Role:
    Defines canonical enumerations for US Federal decennial census schedules
    (CensusYearUS) and genealogical date approximation qualifiers (DateModifier),
    supporting token normalization, GEDCOM date modifier parity, and bounded
    enumeration membership.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Self

from gda.core.enums.base import GDAIntEnum, GDAStrEnum
from gda.core.errors import ModelFormatError

__version__ = "1.0.0+build.5"

__all__ = [
    "CensusYearUS",
    "DateModifier",
    "MODIFIER_ALIASES",
    "normalize_modifier",
]


class CensusYearUS(GDAIntEnum):
    """Valid US Federal Decennial Census enumeration years (1790 to 1950).

    Note: 1890 is intentionally omitted because surviving population schedules
    were destroyed by fire and water damage in 1921.
    """

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

    @classmethod
    def from_raw(cls, raw_value: Any, *, field_name: str | None = None) -> Self:
        """Resolve a DateModifier member or alias token to a canonical DateModifier.

        Args:
            raw_value: DateModifier member or string alias/code to resolve.
            field_name: Optional domain field name included in error diagnostics.

        Returns:
            Canonical DateModifier enum member.

        Raises:
            ModelFormatError: If raw_value is not a string or is an unrecognized modifier.
        """
        if isinstance(raw_value, cls):
            return raw_value

        details: dict[str, Any] = {
            "raw_value": repr(raw_value),
            "raw_type": type(raw_value).__name__,
        }
        if field_name is not None:
            details["field_name"] = field_name

        if not isinstance(raw_value, str):
            raise ModelFormatError(
                f"Invalid DateModifier value: {raw_value!r}",
                details=details,
            )
        token = raw_value.strip().upper()
        matched = MODIFIER_ALIASES.get(token)
        if matched is not None:
            return matched
        raise ModelFormatError(
            f"Invalid DateModifier value: '{raw_value}'.",
            details=details,
        )


MODIFIER_ALIASES: MappingProxyType[str, DateModifier] = MappingProxyType(
    {
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
)


def normalize_modifier(modifier: DateModifier | str | None) -> DateModifier | None:
    """Normalize string, enum, or alias into a valid DateModifier instance.

    Args:
        modifier: Raw date modifier string, DateModifier enum member, or None.

    Returns:
        Canonical DateModifier member, or None if input is None.

    Raises:
        ModelFormatError: If modifier cannot be normalized to a recognized DateModifier.
    """
    if modifier is None:
        return None
    return DateModifier.from_raw(modifier)
