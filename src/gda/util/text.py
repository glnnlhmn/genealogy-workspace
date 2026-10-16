# Name: text.py
# Path: src/gda/util/text.py

"""Pure stateless text normalization, slugging, and historical phonetic algorithms.

Operational Role:
    Provides deterministic string manipulation for archival and genealogical
    intake pipelines, including whitespace cleansing, diacritic stripping,
    ASCII conversion, filesystem/URI slugging, Soundex, and canonical NYSIIS encoding.

Note:
    PRERELEASE: Module is under active development (version 0.0.1+build.r15).
"""

from __future__ import annotations

__version__ = "0.0.1+build.r15"

import re
import unicodedata

__all__ = [
    "clean_whitespace",
    "normalize_ascii",
    "phonetic_nysiis",
    "phonetic_soundex",
    "slugify",
]

_WHITESPACE_RUN_REGEX: re.Pattern[str] = re.compile(r"[ \t\f\v]+")
_SLUG_NON_ALPHANUM_REGEX: re.Pattern[str] = re.compile(r"[^a-z0-9]+")
_ALPHA_FILTER_REGEX: re.Pattern[str] = re.compile(r"[^A-Z]")

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
_SOUNDEX_VOWELS: set[str] = {"A", "E", "I", "O", "U", "Y"}
_VOWELS: set[str] = {"A", "E", "I", "O", "U"}


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


def slugify(text: str, delimiter: str = "-") -> str:
    """Generate a deterministic, lowercase, filesystem- and URI-safe slug.

    Args:
        text: Raw source string to convert.
        delimiter: Separator between alphanumeric words. Defaults to '-'.

    Returns:
        Filesystem- and URI-safe slugified string.

    Raises:
        TypeError: If text is not an instance of str.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}.")

    ascii_text = normalize_ascii(text).lower()
    cleaned = _SLUG_NON_ALPHANUM_REGEX.sub(" ", ascii_text).strip()
    return re.sub(r"\s+", delimiter, cleaned)


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

    while len(encoded_digits) < 3:
        encoded_digits.append("0")

    return f"{first_char}{''.join(encoded_digits[:3])}"


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

    # Step 1: Initial prefix transliteration
    if token.startswith("MAC"):
        token = "MCC" + token[3:]
    elif token.startswith("KN"):
        token = "NN" + token[2:]
    elif token.startswith("K"):
        token = "C" + token[1:]
    elif token.startswith("PH"):
        token = "FF" + token[2:]
    elif token.startswith("PF"):
        token = "FF" + token[2:]
    elif token.startswith("SCH"):
        token = "SSS" + token[3:]

    # Step 2: Terminal suffix transliteration
    if token.endswith(("EE", "IE")):
        token = token[:-2] + "Y"
    elif token.endswith(("DT", "RT", "RD", "NT", "ND")):
        token = token[:-2] + "D"

    # Step 3: Seed key with single first character; collapse duplicate prefix runs
    first_char = token[0]
    key: list[str] = [first_char]

    i = 1
    length = len(token)
    while i < length:
        if token[i] != first_char:
            break
        i += 1

    # Step 4: Iterative scan across the remainder of the token
    while i < length:
        ch = token[i]
        nxt = token[i + 1] if i + 1 < length else ""
        step = 1

        if ch == "E" and nxt == "V":
            replacement = "AF"
            step = 2
        elif ch in _VOWELS:
            replacement = "A"
        elif ch == "Q":
            replacement = "G"
        elif ch == "Z":
            replacement = "S"
        elif ch == "M" and nxt == "P" and (i + 2 < length and token[i + 2] == "B"):
            replacement = "N"
            step = 2
        elif ch == "M":
            replacement = "N"
        elif ch == "K" and nxt == "N":
            replacement = "N"
            step = 2
        elif ch == "K":
            replacement = "C"
        elif ch == "S" and nxt == "C" and (i + 2 < length and token[i + 2] == "H"):
            replacement = "S"
            step = 3
        elif ch == "P" and nxt == "H":
            replacement = "FF"
            step = 2
        elif ch == "H" and (token[i - 1] not in _VOWELS or nxt not in _VOWELS):
            replacement = ""
        elif ch == "W" and token[i - 1] in _VOWELS:
            replacement = ""
        else:
            replacement = ch

        for rep in replacement:
            if rep != key[-1]:
                key.append(rep)

        i += step

    result = "".join(key)

    # Step 5: Terminal suffix cleanup
    if result.endswith("AY"):
        result = result[:-2] + "Y"
    elif result.endswith("S") and len(result) > 1 and not token.endswith("SCH"):
        result = result[:-1]

    if result.endswith("A") and len(result) > 1:
        result = result[:-1]

    return result
