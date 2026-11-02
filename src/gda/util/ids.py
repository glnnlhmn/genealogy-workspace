"""Path: src/gda/util/ids.py

Stateless identifier minting, parsing, formatting, and validation helpers.

Operational Role:
    Provides deterministic RFC 4122 UUIDv4 minting alongside canonical
    sequential smartID minting, validation, decomposition, and high-water
    mark sequence extraction anchored to gda.enums.core and gda.model.atom.id
    without regular expressions.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Any

from gda.core.errors import ModelFormatError, ModelPrefixMismatchError
from gda.enums.core import IDType, SmartIDPrefix
from gda.model.atom.id import (
    AtomID,
    DraftRecordID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    NoteID,
    RepositoryID,
    SiteID,
    UUIDv4Str,
)

__version__ = "0.0.2+build.9"

__all__ = [
    "extract_max_smart_id",
    "mint_smart_id",
    "mint_uuid",
    "parse_smart_id",
    "verify_id",
]

_PREFIX_TO_ATOM_CLASS: dict[SmartIDPrefix, type[AtomID]] = {
    SmartIDPrefix.IND: IndividualID,
    SmartIDPrefix.FID: FactID,
    SmartIDPrefix.LOC: LocationID,
    SmartIDPrefix.SID: SiteID,
    SmartIDPrefix.FAM: FamilyID,
    SmartIDPrefix.NOT: NoteID,
    SmartIDPrefix.REP: RepositoryID,
    SmartIDPrefix.DRF: DraftRecordID,
}


# ==============================================================================
# SECTION 1: PUBLIC VALIDATION GATEWAY & PRIVATE DISPATCH
# ==============================================================================


def verify_id(
    val: str,
    id_type: IDType = IDType.SMART_ID,
    smart_id_prefix: SmartIDPrefix | None = None,
) -> bool:
    """Verify whether a candidate identifier conforms to the specified IDType.

    When id_type is IDType.SMART_ID, optionally validates against a specific
    SmartIDPrefix by inspecting its authoritative AtomID model definition.

    Args:
        val: Required candidate identifier string.
        id_type: Identifier format category (IDType.SMART_ID or IDType.UUID).
        smart_id_prefix: Required or optional prefix constraint when validating smartIDs.

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
        try:
            UUIDv4Str(clean_val)
            return True
        except (ModelFormatError, ValueError):
            return False

    if id_type == IDType.SMART_ID:
        return _validate_smart_id(clean_val, smart_id_prefix)

    return False


def _validate_smart_id(clean_val: str, prefix: SmartIDPrefix | None) -> bool:
    """Validate smartID format against authoritative AtomID model classes."""
    if "-" not in clean_val:
        return False

    parts = clean_val.split("-")
    if len(parts) != 2:
        return False

    parsed_prefix_str, _ = parts
    try:
        parsed_prefix = SmartIDPrefix(parsed_prefix_str)
    except ValueError:
        return False

    if prefix is not None and parsed_prefix != prefix:
        return False

    atom_cls = _PREFIX_TO_ATOM_CLASS.get(parsed_prefix)
    if atom_cls is None:
        return False

    try:
        atom_cls(clean_val)
        return True
    except (ModelFormatError, ModelPrefixMismatchError, ValueError):
        return False


# ==============================================================================
# SECTION 2: IDENTIFIER GENERATION & COMPOSITION
# ==============================================================================


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
        ValueError: If val is None, empty, compound, or fails AtomID validation.
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
    """Extract the highest numeric sequence integer from an iterable of smartIDs.

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
