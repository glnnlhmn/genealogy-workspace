"""Path: src/gda/util/ids.py

Stateless identifier minting, parsing, formatting, and validation helpers.

Operational Role:
    Provides deterministic RFC 4122 UUIDv4 minting alongside canonical
    sequential smartID minting, validation, decomposition, high-water
    mark sequence extraction, and universal identifier string unwrapping
    decoupled from high-level domain models.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Any

from gda.core.enums import IDType, SmartIDPrefix
from gda.core.types import ATOM_ID_REGEX, UUID_V4_REGEX

__version__ = "1.0.0+build.14"

__all__ = [
    "extract_max_smart_id",
    "mint_smart_id",
    "mint_uuid",
    "normalize_id",
    "parse_smart_id",
    "verify_id",
]

_SMART_ID_PATTERN = ATOM_ID_REGEX


def normalize_id(val: Any) -> str:
    """Extract a canonical trimmed string identifier from a string, dict, or value atom.

    Args:
        val: Candidate string, dictionary with a 'value' key, or domain atom
            exposing a '.value' attribute.

    Returns:
        Trimmed canonical identifier string.

    Raises:
        ValueError: If val is None or resolves to an empty/whitespace string.
    """
    if val is None:
        raise ValueError("Cannot normalize identifier from None.")

    if isinstance(val, dict):
        raw = val.get("value", "")
    elif hasattr(val, "value"):
        raw = val.value
    else:
        raw = val

    text = str(raw).strip()
    if not text:
        raise ValueError("Normalized identifier cannot be empty or whitespace.")
    return text


def verify_id(
    val: str,
    id_type: IDType = IDType.SMART_ID,
    smart_id_prefix: SmartIDPrefix | None = None,
) -> bool:
    """Verify whether a candidate identifier conforms to the specified IDType.

    Args:
        val: Required candidate identifier string.
        id_type: Identifier format category (IDType.SMART_ID or IDType.UUID).
        smart_id_prefix: Optional prefix constraint when validating smartIDs.

    Returns:
        True if the candidate string strictly satisfies the format; False otherwise.

    Raises:
        TypeError: If val is not a string.
        ValueError: If smart_id_prefix is provided when id_type is IDType.UUID.
    """
    if not isinstance(val, str):
        raise TypeError(f"Identifier 'val' must be a string, got {type(val).__name__}.")

    clean_val = val.strip()
    if not clean_val:
        return False

    if id_type == IDType.UUID:
        if smart_id_prefix is not None:
            raise ValueError("smart_id_prefix cannot be specified for IDType.UUID.")
        return UUID_V4_REGEX.match(clean_val) is not None

    if id_type == IDType.SMART_ID:
        return _validate_smart_id(clean_val, smart_id_prefix)

    return False


def _validate_smart_id(clean_val: str, prefix: SmartIDPrefix | None) -> bool:
    """Validate smartID format purely against regex and registered SmartIDPrefix members."""
    if not _SMART_ID_PATTERN.match(clean_val):
        return False

    prefix_str, _ = clean_val.split("-", 1)
    try:
        parsed_prefix = SmartIDPrefix(prefix_str)
    except ValueError:
        return False

    if prefix is not None and parsed_prefix != prefix:
        return False

    return True


def mint_uuid() -> str:
    """Mint a new RFC 4122 lowercase UUIDv4 string.

    Returns:
        Canonical lowercase UUIDv4 string.
    """
    return str(uuid.uuid4()).lower()


def mint_smart_id(
    prefix: SmartIDPrefix,
    sequence_num: int,
    padding: int = 6,
) -> str:
    """Mint a canonical zero-padded smartID string from a SmartIDPrefix.

    Args:
        prefix: Canonical SmartIDPrefix enum member.
        sequence_num: Positive integer sequence number.
        padding: Zero-padding width (defaults to 6 per modern AtomID standard).

    Returns:
        Standardized smartID string (e.g., 'LOC-000104').

    Raises:
        ValueError: If sequence_num is negative.
    """
    if sequence_num < 0:
        raise ValueError(f"Sequence number {sequence_num} cannot be negative.")

    return f"{prefix.value}-{sequence_num:0{padding}d}"


def parse_smart_id(val: str | Any) -> tuple[SmartIDPrefix, int]:
    """Decompose a canonical smartID into its SmartIDPrefix and integer sequence.

    Args:
        val: Candidate identifier string or value object exposing a '.value' attribute.

    Returns:
        Tuple of (SmartIDPrefix, sequence_number).

    Raises:
        ValueError: If val is None, empty, compound, or fails format validation.
    """
    raw = getattr(val, "value", val)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("Cannot parse smartID from None or empty input.")

    clean_raw = raw.strip()
    if not _validate_smart_id(clean_raw, prefix=None):
        raise ValueError(
            f"'{clean_raw}' does not conform to canonical smartID format 'PREFIX-######'."
        )

    prefix_str, seq_str = clean_raw.split("-", 1)
    return SmartIDPrefix(prefix_str), int(seq_str)


def extract_max_smart_id(
    id_items: Iterable[Any] | None,
    prefix: SmartIDPrefix | None = None,
    *,
    ignore_errors: bool = True,
) -> int:
    """Extract highest sequence integer from an iterable of smartIDs.

    Args:
        id_items: Iterable of smartID strings or domain value objects.
        prefix: Optional SmartIDPrefix member to restrict the scan.
        ignore_errors: If True, skips invalid or unparseable items; if False, raises ValueError.

    Returns:
        Highest integer sequence discovered, or 0 if empty or no matching smartIDs found.

    Raises:
        ValueError: If ignore_errors is False and an invalid identifier is encountered.
    """
    if not id_items or isinstance(id_items, (str, bytes)):
        return 0

    max_val = 0
    for item in id_items:
        try:
            parsed_prefix, seq_num = parse_smart_id(item)
            if prefix is not None and parsed_prefix != prefix:
                continue
            if seq_num > max_val:
                max_val = seq_num
        except ValueError:
            if not ignore_errors:
                raise

    return max_val
