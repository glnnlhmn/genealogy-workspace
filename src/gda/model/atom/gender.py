"""Path: src/gda/model/atom/gender.py

Biological sex and gender at birth atomic value object representation.

Operational Role:
    Defines the immutable atomic value object ('GenderAtom') representing
    biological sex or gender recorded at birth across historical vital records,
    censuses, and parish registers. Restricts canonical codes strictly to
    'M' (Male), 'F' (Female), and 'U' (Undetermined/Unknown), providing input
    token normalization and total ordering.
"""

from __future__ import annotations

from functools import total_ordering
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.enums.core import Sex

__version__ = "1.0.0+build.1"

__all__ = ["GenderAtom"]

_VALID_CODES: set[str] = {"M", "F", "U"}


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class GenderAtom(IntrospectableMixin):
    """Immutable atomic representation of biological sex or gender recorded at birth."""

    value: str = Field(
        ..., description="Canonical single-character code: 'M', 'F', or 'U'."
    )

    VALID_CODES: ClassVar[set[str]] = _VALID_CODES

    def __post_init__(self) -> None:
        """Enforce strict normalization and membership within M, F, and U."""
        clean = self.value.strip().upper() if isinstance(self.value, str) else ""
        if clean not in self.VALID_CODES:
            raise ModelFormatError(
                f"Invalid GenderAtom code: '{self.value}'. Must be one of ('M', 'F', 'U').",
                details={"value": self.value, "valid_codes": sorted(self.VALID_CODES)},
            )
        object.__setattr__(self, "value", clean)

    @classmethod
    def from_input(cls, raw: str | Sex | GenderAtom | None) -> GenderAtom:
        """Normalize raw transcription tokens or enums into canonical GenderAtom."""
        if raw is None:
            return cls(value="U")
        if isinstance(raw, GenderAtom):
            return raw
        if isinstance(raw, Sex):
            return cls(value=raw.value if raw.value in _VALID_CODES else "U")

        token = str(raw).strip().upper()
        mapping = {
            "M": "M",
            "MALE": "M",
            "BOY": "M",
            "MAN": "M",
            "F": "F",
            "FEMALE": "F",
            "GIRL": "F",
            "WOMAN": "F",
            "U": "U",
            "UNKNOWN": "U",
            "UNDETERMINED": "U",
            "UNRECORDED": "U",
            "?": "U",
        }
        if token in mapping:
            return cls(value=mapping[token])
        raise ModelFormatError(
            f"Cannot normalize '{raw}' to a valid GenderAtom.",
            details={"raw": str(raw)},
        )

    @property
    def is_male(self) -> bool:
        """Return True if male."""
        return self.value == "M"

    @property
    def is_female(self) -> bool:
        """Return True if female."""
        return self.value == "F"

    @property
    def is_undetermined(self) -> bool:
        """Return True if unknown or unrecorded."""
        return self.value == "U"

    def to_enum(self) -> Sex:
        """Convert canonical atom to authoritative Sex enum member."""
        return Sex(self.value)

    def __str__(self) -> str:
        """Return canonical single-character code."""
        return self.value

    def __repr__(self) -> str:
        """Return constructor representation."""
        return f"GenderAtom(value='{self.value}')"

    def __lt__(self, other: Any) -> bool:
        """Support deterministic string and cross-instance ordering."""
        if isinstance(other, GenderAtom):
            return self.value < other.value
        if isinstance(other, str):
            return self.value < other
        return NotImplemented
