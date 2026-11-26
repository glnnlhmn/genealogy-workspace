"""Path: src/gda/core/constants/domain.py

Canonical domain scalar sets, historical year limits, geographic bounds,
and evidentiary scoring invariants.

Operational Role:
    Centralizes immutable scalar bounds for biological gender codes,
    historical calendar years, WGS84 coordinates, QUAY certainty scores,
    Ahnentafel numbering, and algorithmic confidence scores.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "GENDER_CODES",
    "MAX_CONFIDENCE_SCORE",
    "MAX_HISTORICAL_YEAR",
    "MAX_LATITUDE",
    "MAX_LONGITUDE",
    "MAX_QUAY_SCORE",
    "MIN_AHNENTAFEL",
    "MIN_CONFIDENCE_SCORE",
    "MIN_HISTORICAL_YEAR",
    "MIN_LATITUDE",
    "MIN_LONGITUDE",
    "MIN_QUAY_SCORE",
]

GENDER_CODES: frozenset[str] = frozenset({"M", "F", "U"})
MIN_HISTORICAL_YEAR: int = 1000
MAX_HISTORICAL_YEAR: int = 2100

# Geographic WGS84 decimal coordinate boundaries
MIN_LATITUDE: float = -90.0
MAX_LATITUDE: float = 90.0
MIN_LONGITUDE: float = -180.0
MAX_LONGITUDE: float = 180.0

# Evidentiary certainty, pedigree numbering, and algorithmic confidence bounds
MIN_QUAY_SCORE: int = 0
MAX_QUAY_SCORE: int = 3
MIN_AHNENTAFEL: int = 1
MIN_CONFIDENCE_SCORE: float = 0.0
MAX_CONFIDENCE_SCORE: float = 1.0
