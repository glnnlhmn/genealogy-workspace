"""Path: src/gda/util/ids.py

Stateless identifier minting, parsing, formatting, and validation helpers.

Operational Role:
    Provides deterministic RFC 4122 UUIDv4 minting alongside canonical
    sequential smartID minting, validation, decomposition, high-water
    mark sequence extraction, polymorphic target ID dispatch, and universal
    identifier/primitive unwrapping decoupled from high-level domain models.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from typing import Any

from gda.core.enums import IDType, SmartIDPrefix
from gda.core.errors import ModelFormatError
from gda.core.types import ATOM_ID_REGEX, UUID_V4_REGEX

__version__ = "1.0.0+build.16"

__all__ = [
    "extract_max_smart_id",
    "mint_smart_id",
    "mint_uuid",
    "normalize_id",
    "parse_smart_id",
    "resolve_polymorphic_id",
    "unwrap_bool_int",
    "unwrap_int",
    "unwrap_value",
    "verify_id",
]

_SMART_ID_PATTERN = ATOM_ID_REGEX


def unwrap_value(val: Any) -> Any:
    """Unwrap an optional GDA atom or enum into its underlying primitive value.

    Args:
        val: Candidate value, None, or domain object exposing a '.value' attribute.

    Returns:
        None if val is None, val.value if present, otherwise val unchanged.
    """
    if val is None:
        return None
    if hasattr(val, "value"):
        return val.value
    return val


def unwrap_int(val: Any) -> int | None:
    """Unwrap an optional integer, IntEnum, or integer-valued atom into an int.

    Args:
        val: Candidate integer, IntEnum, atom, or None.

    Returns:
        Integer value or None if val is None.

    Raises:
        ValueError: If val is a boolean or cannot be converted to an integer.
    """
    if val is None:
        return None
    raw = val.value if hasattr(val, "value") else val
    if isinstance(val, bool) or isinstance(raw, bool):
        raise ValueError(f"Boolean value '{val}' cannot be unwrapped as an integer.")
    return int(raw)


def unwrap_bool_int(val: bool | int | None) -> int | None:
    """Convert an optional boolean or integer flag into SQLite integer format (1, 0, or None).

    Args:
        val: Optional boolean flag or integer 1/0.

    Returns:
        1 for truthy, 0 for falsy, or None if val is None.
    """
    if val is None:
        return None
    return 1 if bool(val) else 0


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
        return _validate_smart_id(clean_val, expected_prefix=smart_id_prefix)

    return False


def _validate_smart_id(
    candidate: str,
    expected_prefix: SmartIDPrefix | None = None,
) -> bool:
    """Validate internal smartID structural pattern and prefix membership."""
    parts = candidate.split("-")
    if len(parts) != 2:
        return False

    raw_prefix, _ = parts
    try:
        resolved_prefix = SmartIDPrefix(raw_prefix)
    except ValueError:
        return False

    if expected_prefix is not None and resolved_prefix != expected_prefix:
        return False

    return _SMART_ID_PATTERN.match(candidate) is not None


def _coerce_prefix(prefix: SmartIDPrefix | str) -> SmartIDPrefix:
    """Resolve a SmartIDPrefix enum member or raw prefix string."""
    return prefix if isinstance(prefix, SmartIDPrefix) else SmartIDPrefix(str(prefix).strip())


def mint_uuid() -> str:
    """Mint a canonical lowercase RFC 4122 UUIDv4 string.

    Returns:
        Lowercase 36-character UUIDv4 string.
    """
    return str(uuid.uuid4()).lower()


def mint_smart_id(
    prefix: SmartIDPrefix | str,
    sequence_num: int,
    padding: int = 6,
) -> str:
    """Mint a zero-padded sequential smartID from a canonical prefix and integer.

    Args:
        prefix: SmartIDPrefix enum member or valid prefix string (e.g., 'LOC').
        sequence_num: Non-negative integer sequence number.
        padding: Digit width for zero-padding (defaults to 6).

    Returns:
        Canonical formatted smartID string (e.g., 'LOC-000042').

    Raises:
        ValueError: If prefix is invalid, sequence_num is negative, or padding < 1.
    """
    if sequence_num < 0:
        raise ValueError(f"Sequence number cannot be negative: {sequence_num}.")
    if padding < 1:
        raise ValueError(f"Padding width must be at least 1: {padding}.")

    resolved_prefix = _coerce_prefix(prefix)
    return f"{resolved_prefix.value}-{sequence_num:0{padding}d}"


def parse_smart_id(val: Any) -> tuple[SmartIDPrefix, int]:
    """Decompose a smartID string or atom into its SmartIDPrefix and integer sequence.

    Args:
        val: SmartID string or domain atom exposing a '.value' attribute.

    Returns:
        Tuple of (SmartIDPrefix, integer sequence number).

    Raises:
        ValueError: If val is empty or does not conform to canonical smartID syntax.
    """
    raw_str = val.value if hasattr(val, "value") else val
    if not isinstance(raw_str, str) or not raw_str.strip():
        raise ValueError(f"Cannot parse smartID from empty or non-string value: {val!r}.")

    clean_val = raw_str.strip()
    if not _validate_smart_id(clean_val):
        raise ValueError(f"Identifier '{clean_val}' does not conform to canonical smartID format.")

    prefix_part, num_part = clean_val.split("-")
    return SmartIDPrefix(prefix_part), int(num_part)


def extract_max_smart_id(
    id_items: Iterable[Any] | None,
    prefix: SmartIDPrefix | str | None = None,
    ignore_errors: bool = True,
) -> int:
    """Determine the highest integer sequence number across an iterable of smartIDs.

    Args:
        id_items: Iterable of smartID strings or domain ID atoms.
        prefix: Optional SmartIDPrefix filter; items with other prefixes are skipped.
        ignore_errors: When True, malformed entries are ignored rather than raising.

    Returns:
        Highest integer sequence number found, or 0 if no matching identifiers exist.

    Raises:
        ValueError: If ignore_errors is False and a malformed smartID is encountered.
    """
    if id_items is None or isinstance(id_items, (str, bytes)):
        return 0

    target_prefix = _coerce_prefix(prefix) if prefix is not None else None
    max_seq = 0
    for item in id_items:
        try:
            item_prefix, seq = parse_smart_id(item)
        except ValueError:
            if not ignore_errors:
                raise
            continue

        if target_prefix in (None, item_prefix) and seq > max_seq:
            max_seq = seq

    return max_seq


def _match_polymorphic_string(
    cleaned: str,
    prefix_map: Mapping[SmartIDPrefix | str, type[Any]] | None,
    uuid_cls: type[Any] | None,
) -> Any | None:
    """Attempt to instantiate an AtomID or UUIDv4Str subclass from a cleaned string."""
    if prefix_map and verify_id(cleaned, id_type=IDType.SMART_ID):
        resolved_prefix, _ = parse_smart_id(cleaned)
        target_cls = prefix_map.get(resolved_prefix) or prefix_map.get(resolved_prefix.value)
        if target_cls is not None:
            return target_cls(cleaned)

    if uuid_cls is not None and verify_id(cleaned, id_type=IDType.UUID):
        return uuid_cls(cleaned)

    return None


def resolve_polymorphic_id(
    raw: Any,
    *,
    prefix_map: Mapping[SmartIDPrefix | str, type[Any]] | None = None,
    uuid_cls: type[Any] | None = None,
    field_name: str = "target_id",
) -> Any:
    """Resolve a polymorphic identifier into its typed AtomID or UUIDv4Str instance.

    Accepts an already-instantiated domain ID (if its type is registered in
    prefix_map or matches uuid_cls), a smartID string dispatched by its prefix,
    or a UUIDv4 string dispatched to uuid_cls.

    Args:
        raw: Candidate identifier instance or raw string.
        prefix_map: Mapping of SmartIDPrefix (or prefix string) to AtomID classes.
        uuid_cls: Optional UUIDv4Str subclass for resolving UUID strings.
        field_name: Field label included in ModelFormatError details on failure.

    Returns:
        Instantiated AtomID or UUIDv4Str subclass corresponding to raw.

    Raises:
        ModelFormatError: If raw is not a valid string/ID or does not match any
            allowed prefix or UUID class.
    """
    allowed_types = tuple(prefix_map.values()) if prefix_map else ()
    if (allowed_types and isinstance(raw, allowed_types)) or (
        uuid_cls is not None and isinstance(raw, uuid_cls)
    ):
        return raw

    if not isinstance(raw, str) or not raw.strip():
        raise ModelFormatError(
            f"Invalid {field_name}: '{raw}' must be a non-empty identifier string.",
            error_code="ERR_MODEL_FORMAT",
            details={"field": field_name, "value": repr(raw)},
        )

    matched = _match_polymorphic_string(raw.strip(), prefix_map, uuid_cls)
    if matched is not None:
        return matched

    raise ModelFormatError(
        f"Invalid {field_name}: '{raw}' does not match any supported identifier type.",
        error_code="ERR_MODEL_FORMAT",
        details={"field": field_name, "value": raw},
    )
