"""Path: src/gda/util/text.py

Pure stateless text normalization, slugging, and historical phonetic algorithms.

Operational Role:
    Provides deterministic string manipulation for archival and genealogical
    intake pipelines, including whitespace cleansing, required-string validation,
    ordered string-list deduplication, diacritic stripping, ASCII conversion,
    filesystem/URI slugging, Soundex, and canonical NYSIIS encoding.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Any

from gda.core.errors import ModelFormatError

__version__ = "1.0.0+build.17"

__all__ = [
    "clean_string",
    "clean_unique_strings",
    "clean_whitespace",
    "normalize_ascii",
    "phonetic_nysiis",
    "phonetic_soundex",
    "require_non_empty",
    "slugify",
]

# Pre-compiled regular expressions for whitespace, punctuation, and alpha filtering
_WHITESPACE_RUN_REGEX: re.Pattern[str] = re.compile(r"[ \t\f\v]+")
_ANY_WHITESPACE_REGEX: re.Pattern[str] = re.compile(r"\s+")
_SLUG_NON_ALPHANUM_REGEX: re.Pattern[str] = re.compile(r"[^a-z0-9]+")
_SLUG_COLON_DELIM_REGEX: re.Pattern[str] = re.compile(r"[\s\-]+")
_ALPHA_FILTER_REGEX: re.Pattern[str] = re.compile(r"[^A-Z]")

_ENCLOSING_PUNCTUATION_PATTERN: re.Pattern[str] = re.compile(r"^[@#*\"'<>]+|[@#*\"'<>]+$")
_REPLACE_CHARACTERS_PATTERN: re.Pattern[str] = re.compile(r"[_*?~^=]+")
_URN_CLEAN_TOKEN_PATTERN: re.Pattern[str] = re.compile(r"[^a-z0-9_:]+")

# American Soundex consonant classification table
_SOUNDEX_DIGITS: dict[str, str] = {
    "B": "1",
    "F": "1",
    "P": "1",
    "V": "1",
    "C": "2",
    "G": "2",
    "J": "2",
    "K": "2",
    "Q": "2",
    "S": "2",
    "X": "2",
    "Z": "2",
    "D": "3",
    "T": "3",
    "L": "4",
    "M": "5",
    "N": "5",
    "R": "6",
}
_SOUNDEX_VOWELS: frozenset[str] = frozenset({"A", "E", "I", "O", "U", "Y"})
_VOWELS: frozenset[str] = frozenset({"A", "E", "I", "O", "U"})

# Declarative Taft (1970) NYSIIS prefix, suffix, and character replacement tables
_NYSIIS_PREFIX_RULES: tuple[tuple[str, str], ...] = (
    ("MAC", "MCC"),
    ("SCH", "SSS"),
    ("KN", "NN"),
    ("PH", "FF"),
    ("PF", "FF"),
    ("K", "C"),
)

_NYSIIS_SUFFIX_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("EE", "IE"), "Y"),
    (("DT", "RT", "RD", "NT", "ND"), "D"),
)

_NYSIIS_MULTI_CHAR_RULES: tuple[tuple[str, str, int], ...] = (
    ("EV", "AF", 2),
    ("MPB", "N", 2),
    ("KN", "N", 2),
    ("SCH", "S", 3),
    ("PH", "FF", 2),
)

_NYSIIS_SINGLE_CHAR_MAP: dict[str, str] = {
    "A": "A",
    "E": "A",
    "I": "A",
    "O": "A",
    "U": "A",
    "Q": "G",
    "Z": "S",
    "M": "N",
    "K": "C",
}


def clean_string(val: Any) -> str | None:
    """Clean string by stripping enclosing delimiters, substituting separators, and trimming.

    Args:
        val: Arbitrary candidate value to clean.

    Returns:
        Trimmed, normalized string with collapsed internal spaces, or None if empty/non-string.
    """
    # Guard against non-string inputs
    if not isinstance(val, str):
        return None

    cleaned = val.strip()
    cleaned = _ENCLOSING_PUNCTUATION_PATTERN.sub("", cleaned).strip()
    cleaned = _REPLACE_CHARACTERS_PATTERN.sub(" ", cleaned)
    cleaned = _ANY_WHITESPACE_REGEX.sub(" ", cleaned).strip()

    return cleaned if cleaned else None


def require_non_empty(val: Any, field_name: str = "value") -> str:
    """Validate that an input is a non-empty string after trimming whitespace.

    Args:
        val: Candidate string value to validate.
        field_name: Field label included in the error message and diagnostic details.

    Returns:
        Trimmed non-empty string.

    Raises:
        ModelFormatError: If val is not a string or is empty/whitespace-only.
    """
    if not isinstance(val, str) or not val.strip():
        raise ModelFormatError(
            f"Field '{field_name}' must be a non-empty string.",
            error_code="ERR_MODEL_FORMAT",
            details={"field": field_name, "value": val},
        )
    return val.strip()


def clean_unique_strings(items: Iterable[Any] | None) -> list[str]:
    """Sanitize an iterable of strings, dropping blanks and deduplicating in order.

    Trims each string item (via clean_string when punctuation cleaning applies or
    standard strip), filters out empty entries, and preserves first-seen order.

    Args:
        items: Optional iterable of candidate strings.

    Returns:
        Ordered list of unique, non-empty trimmed strings.

    Raises:
        ModelFormatError: If any non-None element in items is not a string.
    """
    if items is None:
        return []

    seen: set[str] = set()
    result: list[str] = []
    for raw in items:
        if raw is None:
            continue
        if not isinstance(raw, str):
            raise ModelFormatError(
                f"Expected str in string collection, got {type(raw).__name__}.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": repr(raw)},
            )
        cleaned = raw.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def clean_whitespace(text: str) -> str:
    """Normalize internal linebreaks, collapse horizontal whitespace, and trim boundaries.

    Args:
        text: Raw source string.

    Returns:
        Cleaned string with unified linebreaks and collapsed spaces.

    Raises:
        TypeError: If text is not an instance of str.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}.")

    # Normalize CRLF/CR to LF and collapse horizontal whitespace runs on each line
    lines = [
        _WHITESPACE_RUN_REGEX.sub(" ", line).strip()
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    return "\n".join(lines).strip()


def normalize_ascii(text: str) -> str:
    """Strip diacritics and convert non-ASCII characters to standard ASCII equivalents.

    Args:
        text: Raw source string containing accents or Unicode characters.

    Returns:
        Decomposed ASCII string with diacritics removed.

    Raises:
        TypeError: If text is not an instance of str.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}.")

    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def slugify(text: str, delimiter: str = "-", allow_colons: bool = False) -> str:
    """Generate a deterministic, lowercase, filesystem- and URI-safe slug.

    Args:
        text: Raw source string to convert.
        delimiter: Separator between alphanumeric words. Defaults to '-'.
        allow_colons: If True, preserves colons for URN segment paths. Defaults to False.

    Returns:
        Filesystem- and URI-safe slugified string.

    Raises:
        TypeError: If text is not an instance of str.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}.")

    ascii_text = normalize_ascii(text).lower()

    if allow_colons:
        cleaned = _SLUG_COLON_DELIM_REGEX.sub(delimiter, ascii_text.strip())
        cleaned = _URN_CLEAN_TOKEN_PATTERN.sub("", cleaned)
        cleaned = re.sub(rf"{re.escape(delimiter)}+", delimiter, cleaned)
        return cleaned.strip(f":-_ {delimiter}")

    cleaned = _SLUG_NON_ALPHANUM_REGEX.sub(" ", ascii_text).strip()
    return _ANY_WHITESPACE_REGEX.sub(delimiter, cleaned)


def phonetic_soundex(name: str) -> str:
    """Encode an English surname or name token using the standard American Soundex algorithm.

    Args:
        name: Name string to encode.

    Returns:
        Four-character Soundex code (e.g., 'S530'). Returns '0000' if no alphabetic characters.

    Raises:
        TypeError: If name is not an instance of str.
    """
    if not isinstance(name, str):
        raise TypeError(f"Expected str, got {type(name).__name__}.")

    ascii_name = normalize_ascii(name).upper()
    letters = _ALPHA_FILTER_REGEX.sub("", ascii_name)
    if not letters:
        return "0000"

    first_char = letters[0]
    encoded_digits: list[str] = []
    prev_code = _SOUNDEX_DIGITS.get(first_char, "")

    # Scan remaining letters, collapsing adjacent identical Soundex digits
    for char in letters[1:]:
        if char in _SOUNDEX_DIGITS:
            code = _SOUNDEX_DIGITS[char]
            if code != prev_code:
                encoded_digits.append(code)
                if len(encoded_digits) == 3:
                    break
            prev_code = code
        elif char in _SOUNDEX_VOWELS:
            prev_code = "0"

    return f"{first_char}{''.join(encoded_digits):0<3}"


def _apply_nysiis_prefix_and_suffix(token: str) -> str:
    """Apply canonical NYSIIS initial prefix and terminal suffix substitutions."""
    for prefix, replacement in _NYSIIS_PREFIX_RULES:
        if token.startswith(prefix):
            token = replacement + token[len(prefix) :]
            break

    for suffixes, replacement in _NYSIIS_SUFFIX_RULES:
        if token.endswith(suffixes):
            token = token[:-2] + replacement
            break

    return token


def _translate_nysiis_position(token: str, index: int) -> tuple[str, int]:
    """Translate the character or digraph at token[index] into its NYSIIS phonetic code.

    Args:
        token: Uppercase alphabetic token after prefix/suffix normalization.
        index: Current scan index (>= 1).

    Returns:
        Tuple of (replacement characters, index step advance).
    """
    window = token[index : index + 3]

    # Check multi-character digraph/trigraph rules (EV, MPB, KN, SCH, PH)
    for pattern, replacement, step in _NYSIIS_MULTI_CHAR_RULES:
        if window.startswith(pattern):
            return replacement, step

    ch = token[index]
    if ch in _NYSIIS_SINGLE_CHAR_MAP:
        return _NYSIIS_SINGLE_CHAR_MAP[ch], 1

    prev_ch = token[index - 1]
    next_ch = token[index + 1] if index + 1 < len(token) else ""

    # Drop H when neither the preceding nor following character is a vowel
    if ch == "H" and (prev_ch not in _VOWELS or next_ch not in _VOWELS):
        return "", 1

    # Drop W when immediately preceded by a vowel
    if ch == "W" and prev_ch in _VOWELS:
        return "", 1

    return ch, 1


def _finalize_nysiis_suffix(result: str, original_token: str) -> str:
    """Apply terminal NYSIIS cleanup rules for trailing 'AY', 'S', and 'A'."""
    if result.endswith("AY"):
        result = result[:-2] + "Y"
    elif result.endswith("S") and len(result) > 1 and not original_token.endswith("SCH"):
        result = result[:-1]

    if result.endswith("A") and len(result) > 1:
        result = result[:-1]

    return result


def phonetic_nysiis(name: str) -> str:
    """Encode a surname or name token using the canonical Refined NYSIIS algorithm (Taft, 1970).

    Args:
        name: Name string to encode.

    Returns:
        Uppercase NYSIIS phonetic code. Returns empty string if no alphabetic characters.

    Raises:
        TypeError: If name is not an instance of str.
    """
    if not isinstance(name, str):
        raise TypeError(f"Expected str, got {type(name).__name__}.")

    ascii_name = normalize_ascii(name).upper()
    token = _ALPHA_FILTER_REGEX.sub("", ascii_name)
    if not token:
        return ""

    # --- Step 1: Initial Prefix & Terminal Suffix Transliteration ---
    token = _apply_nysiis_prefix_and_suffix(token)

    # --- Step 2: Seed Key & Skip Duplicate Initial Character Runs ---
    first_char = token[0]
    key: list[str] = [first_char]
    length = len(token)
    index = 1
    while index < length and token[index] == first_char:
        index += 1

    # --- Step 3: Iterative Digraph & Consonant Scan ---
    while index < length:
        replacement, step = _translate_nysiis_position(token, index)
        for rep in replacement:
            if rep != key[-1]:
                key.append(rep)
        index += step

    # --- Step 4: Terminal Suffix Cleanup ---
    return _finalize_nysiis_suffix("".join(key), token)
