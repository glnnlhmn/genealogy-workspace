# Name: ids.py
# Path: src/gda/util/ids.py

"""Stateless identifier minting, parsing, formatting, and validation helpers.

Operational Role:
    Provides deterministic RFC 4122 UUIDv4 minting and validation alongside
    canonical sequential 5-digit entity ID validation, formatting, and decomposition
    anchored to gda.types.primitives.

Note:
    PRERELEASE: Module is under active development (version 0.0.1+build.1).
"""

from __future__ import annotations

import re
import uuid

from gda.types.primitives import ENTITY_ID_PATTERNS, UUID_V4_REGEX

__version__ = "0.0.1+build.1"

__all__ = [
    "format_entity_id",
    "is_valid_entity_id",
    "is_valid_location_id",
    "is_valid_note_id",
    "is_valid_person_id",
    "is_valid_repository_id",
    "is_valid_site_id",
    "is_valid_uuid",
    "mint_uuid",
    "parse_entity_id",
]

_COMPILED_ENTITY_REGEXES: dict[str, re.Pattern[str]] = {
    prefix: re.compile(pattern) for prefix, pattern in ENTITY_ID_PATTERNS.items()
}
_GENERAL_ENTITY_ID_REGEX: re.Pattern[str] = re.compile(r"^[A-Z]{3}-\d{5}$")


def mint_uuid() -> str:
    """Mint a new RFC 4122 lowercase UUIDv4 string.

    Returns:
        Canonical lowercase UUIDv4 string.
    """
    return str(uuid.uuid4()).lower()


def is_valid_uuid(val: str | None) -> bool:
    """Verify whether a string conforms to lowercase RFC 4122 UUIDv4 syntax.

    Args:
        val: Candidate string to inspect.

    Returns:
        True if string is a valid lowercase UUIDv4; False otherwise.
    """
    if not val or not isinstance(val, str):
        return False
    return bool(UUID_V4_REGEX.match(val.strip()))


def is_valid_entity_id(val: str | None, prefix: str | None = None) -> bool:
    """Verify whether a string matches sequential 5-digit entity ID syntax.

    Args:
        val: Candidate identifier string.
        prefix: Optional specific 3-letter prefix (e.g., 'IND', 'LOC'). If None,
            validates against any canonical prefix registered in ENTITY_ID_PATTERNS.

    Returns:
        True if string conforms to the entity ID pattern; False otherwise.
    """
    if not val or not isinstance(val, str):
        return False

    clean_val = val.strip()

    if prefix is not None:
        clean_prefix = prefix.strip().upper()
        regex = _COMPILED_ENTITY_REGEXES.get(clean_prefix)
        if regex is None:
            return False
        return bool(regex.match(clean_val))

    for regex in _COMPILED_ENTITY_REGEXES.values():
        if regex.match(clean_val):
            return True
    return False


def is_valid_person_id(val: str | None) -> bool:
    """Verify whether a string is a valid Person identifier (IND-#####).

    Args:
        val: Candidate identifier string.

    Returns:
        True if string matches IND-##### pattern; False otherwise.
    """
    return is_valid_entity_id(val, prefix="IND")


def is_valid_location_id(val: str | None) -> bool:
    """Verify whether a string is a valid Location identifier (LOC-#####).

    Args:
        val: Candidate identifier string.

    Returns:
        True if string matches LOC-##### pattern; False otherwise.
    """
    return is_valid_entity_id(val, prefix="LOC")


def is_valid_site_id(val: str | None) -> bool:
    """Verify whether a string is a valid Site identifier (SID-#####).

    Args:
        val: Candidate identifier string.

    Returns:
        True if string matches SID-##### pattern; False otherwise.
    """
    return is_valid_entity_id(val, prefix="SID")


def is_valid_note_id(val: str | None) -> bool:
    """Verify whether a string is a valid Note identifier (NOT-#####).

    Args:
        val: Candidate identifier string.

    Returns:
        True if string matches NOT-##### pattern; False otherwise.
    """
    return is_valid_entity_id(val, prefix="NOT")


def is_valid_repository_id(val: str | None) -> bool:
    """Verify whether a string is a valid Custodial Repository identifier (REP-#####).

    Args:
        val: Candidate identifier string.

    Returns:
        True if string matches REP-##### pattern; False otherwise.
    """
    return is_valid_entity_id(val, prefix="REP")


def format_entity_id(prefix: str, sequence_num: int) -> str:
    """Format an entity prefix and integer sequence into a zero-padded 5-digit identifier.

    Args:
        prefix: Canonical 3-letter entity prefix (e.g., 'IND', 'LOC', 'SID').
        sequence_num: Positive integer sequence number.

    Returns:
        Standardized identifier string (e.g., 'IND-00042').

    Raises:
        ValueError: If prefix is unregistered or sequence_num is negative or exceeds 99999.
    """
    clean_prefix = prefix.strip().upper()
    if clean_prefix not in _COMPILED_ENTITY_REGEXES:
        raise ValueError(
            f"Unrecognized entity prefix '{prefix}'. "
            f"Expected one of: {sorted(_COMPILED_ENTITY_REGEXES.keys())}"
        )
    if sequence_num < 0 or sequence_num > 99999:
        raise ValueError(
            f"Sequence number {sequence_num} is out of allowable range (0-99999)."
        )
    return f"{clean_prefix}-{sequence_num:05d}"


def parse_entity_id(val: str | None) -> tuple[str, int]:
    """Decompose a sequential entity identifier into its prefix and integer sequence.

    Args:
        val: Candidate identifier string (e.g., 'LOC-00105').

    Returns:
        Tuple of (prefix, sequence_number).

    Raises:
        ValueError: If val is None, empty, or not a valid sequential entity ID.
    """
    if not val or not isinstance(val, str):
        raise ValueError("Cannot parse entity ID from None or empty input.")

    clean_val = val.strip()
    match = _GENERAL_ENTITY_ID_REGEX.match(clean_val)
    if not match:
        raise ValueError(
            f"'{val}' does not conform to entity identifier format 'PREFIX-00000'."
        )

    prefix, seq_str = clean_val.split("-", 1)
    if prefix not in _COMPILED_ENTITY_REGEXES:
        raise ValueError(
            f"Prefix '{prefix}' in '{val}' is not a registered canonical entity prefix."
        )

    return prefix, int(seq_str)
