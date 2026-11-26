"""Path: tests/test_gda/test_core/strategies.py

Reusable Hypothesis property-testing strategies for Tier 0 (gda.core) suites.

Operational Role:
    Centralizes deterministic, composable Hypothesis strategies for historical
    dates, UTC timestamps, strict/adversarial numeric inputs, binary streaming
    payloads, enum casing/separator/whitespace mutations, and exotic logging
    payloads. Higher-tier test suites (model, entity, db) may import and compose
    these Tier-0-safe generators directly.
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from hypothesis import strategies as st

__version__ = "1.0.0+build.2"

__all__ = [
    "binary_and_chunk_size",
    "bool_or_non_int",
    "enum_token_variants",
    "exotic_log_details",
    "historical_date_pairs",
    "historical_dates",
    "iso_date_strings",
    "non_finite_floats",
    "strict_ints",
    "utc_timestamps",
]


# ==============================================================================
# SECTION 1: HISTORICAL DATES & UTC TIMESTAMPS (dates.py, types.py)
# Note: Covers leap years, century boundaries, and partial ISO date formats.
# ==============================================================================


def historical_dates(
    min_year: int = 1500,
    max_year: int = 2100,
) -> st.SearchStrategy[date]:
    """Generate valid Gregorian calendar dates across genealogical eras."""
    return st.dates(
        min_value=date(min_year, 1, 1),
        max_value=date(max_year, 12, 31),
    )


@st.composite
def historical_date_pairs(
    draw: st.DrawFn,
    min_year: int = 1500,
    max_year: int = 2100,
) -> tuple[date, date]:
    """Generate an ordered (earlier, later) pair of historical dates."""
    d1 = draw(historical_dates(min_year=min_year, max_year=max_year))
    d2 = draw(historical_dates(min_year=min_year, max_year=max_year))
    return (d1, d2) if d1 <= d2 else (d2, d1)


@st.composite
def iso_date_strings(draw: st.DrawFn) -> str:
    """Generate valid YYYY, YYYY-MM, or YYYY-MM-DD genealogical ISO date strings."""
    d = draw(historical_dates())
    precision = draw(st.sampled_from(("year", "month", "day")))
    if precision == "year":
        return f"{d.year:04d}"
    if precision == "month":
        return f"{d.year:04d}-{d.month:02d}"
    return d.isoformat()


@st.composite
def utc_timestamps(draw: st.DrawFn) -> str:
    """Generate canonical Zulu UTC ISO-8601 timestamp strings."""
    dt = draw(
        st.datetimes(
            min_value=datetime(1970, 1, 1),
            max_value=datetime(2100, 12, 31, 23, 59, 59),
        )
    )
    return dt.replace(tzinfo=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ==============================================================================
# SECTION 2: STRICT NUMERIC & ADVERSARIAL INPUTS (types.py, config.py, hashes.py)
# Note: Targets bool-as-int traps and NaN/Inf coercion bugs.
# ==============================================================================


def strict_ints(
    min_value: int = -1_000_000,
    max_value: int = 1_000_000,
) -> st.SearchStrategy[int]:
    """Generate true integers (never booleans) within the specified bounds."""
    return st.integers(min_value=min_value, max_value=max_value)


def non_finite_floats() -> st.SearchStrategy[float]:
    """Generate non-finite IEEE 754 floats (NaN, +Inf, -Inf)."""
    return st.sampled_from((math.nan, math.inf, -math.inf))


def bool_or_non_int() -> st.SearchStrategy[Any]:
    """Generate values that must be rejected by strict integer guards."""
    return st.one_of(
        st.booleans(),
        st.floats(allow_nan=True, allow_infinity=True),
        st.text(max_size=12),
        st.none(),
        st.lists(st.integers(), max_size=3),
    )


# ==============================================================================
# SECTION 3: BINARY PAYLOADS & STREAMING CHUNK SIZES (hashes.py)
# Note: Verifies sha256_file chunk-size invariance across arbitrary boundaries.
# ==============================================================================


@st.composite
def binary_and_chunk_size(draw: st.DrawFn) -> tuple[bytes, int]:
    """Generate an arbitrary byte payload paired with a valid positive chunk size."""
    payload = draw(st.binary(min_size=0, max_size=8192))
    chunk_size = draw(st.integers(min_value=1, max_value=4096))
    return payload, chunk_size


# ==============================================================================
# SECTION 4: ENUM TOKEN, SEPARATOR & CASING MUTATIONS (enums/coercion.py)
# Note: Fuzzes coerce_enum against mixed casing, separators (-, space), and padding.
# ==============================================================================


@st.composite
def enum_token_variants(draw: st.DrawFn, enum_cls: type[Enum]) -> tuple[Enum, Any]:
    """Generate a (canonical_member, mutated_input) pair for any StrEnum or IntEnum."""
    member = draw(st.sampled_from(list(enum_cls)))
    val = member.value

    if isinstance(val, str):
        variant_mode = draw(
            st.sampled_from(("exact", "lower", "upper", "title", "hyphen", "space", "padded"))
        )
        if variant_mode == "lower":
            mutated: Any = val.lower()
        elif variant_mode == "upper":
            mutated = val.upper()
        elif variant_mode == "title":
            mutated = val.title()
        elif variant_mode == "hyphen":
            mutated = val.replace("_", "-").lower()
        elif variant_mode == "space":
            mutated = val.replace("_", " ").lower()
        elif variant_mode == "padded":
            pad_left = draw(st.sampled_from(("", " ", "\t")))
            pad_right = draw(st.sampled_from(("", " ", "\n")))
            mutated = f"{pad_left}{val}{pad_right}"
        else:
            mutated = val
        return member, mutated

    # IntEnum or other non-string enum: return member, raw int, or stringified int.
    return member, draw(st.sampled_from((member, val, str(val), f" {val} ")))


# ==============================================================================
# SECTION 5: EXOTIC LOGGING PAYLOADS (logging.py)
# Note: Exercises JsonFormatter against non-JSON-native Python objects.
# ==============================================================================


@st.composite
def exotic_log_details(draw: st.DrawFn) -> dict[str, Any]:
    """Generate structured log detail dicts containing non-JSON-native Python objects."""
    label = draw(st.text(min_size=1, max_size=24))
    count = draw(st.integers(min_value=0, max_value=100))
    return {
        "label": label,
        "count": count,
        "path": Path("runtime") / "sample.db",
        "tags": frozenset({"alpha", "beta"}),
        "raw_bytes": b"gda",
    }
