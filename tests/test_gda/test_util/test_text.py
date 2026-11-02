"""Path: tests/test_gda/test_util/test_text.py

Unit and regression test suite for pure stateless text utilities.

Operational Role:
    Verifies string normalization, whitespace cleansing, ASCII transliteration,
    filesystem/URI slugging, Soundex, and NYSIIS phonetic algorithms.
"""

from __future__ import annotations

import pytest

from gda.util.text import (
    clean_string,
    clean_whitespace,
    normalize_ascii,
    phonetic_nysiis,
    phonetic_soundex,
    slugify,
)

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: STRING SANITIZATION & DELIMITER STRIPPING (clean_string)
# ==============================================================================


@pytest.mark.unit
def test_clean_string_valid_strings_stripped_and_normalized() -> None:
    """Verify clean_string strips enclosing punctuation and normalizes separators."""
    assert clean_string("  @#*John Doe*#@  ") == "John Doe"
    assert clean_string("<<Jane_Doe>>") == "Jane Doe"
    assert clean_string("Alice?Bob~Charlie") == "Alice Bob Charlie"
    assert clean_string("   Clean Text   ") == "Clean Text"


@pytest.mark.regression
def test_clean_string_non_string_or_empty_returns_none() -> None:
    """Verify clean_string returns None for non-strings, pure whitespace, or delimiters."""
    assert clean_string(None) is None
    assert clean_string(12345) is None
    assert clean_string([]) is None
    assert clean_string("") is None
    assert clean_string("     ") is None
    assert clean_string("@#*\"'<>") is None
    assert clean_string("___***???") is None


# ==============================================================================
# GROUP 2: WHITESPACE NORMALIZATION (clean_whitespace)
# ==============================================================================


@pytest.mark.unit
def test_clean_whitespace_normalizes_linebreaks_and_internal_runs() -> None:
    """Verify clean_whitespace collapses spaces and unifies CRLF to standard LF."""
    raw = "Line 1   with   spaces\r\n\r\nLine 2\t\twith tabs\rLine 3\n"
    expected = "Line 1 with spaces\n\nLine 2 with tabs\nLine 3"
    assert clean_whitespace(raw) == expected


@pytest.mark.unit
def test_clean_whitespace_empty_or_pure_whitespace_returns_empty() -> None:
    """Verify clean_whitespace returns empty string for blank text."""
    assert clean_whitespace("   \t\n\r   ") == ""
    assert clean_whitespace("") == ""


@pytest.mark.regression
def test_clean_whitespace_non_string_raises_type_error() -> None:
    """Verify clean_whitespace rejects non-string inputs with TypeError."""
    with pytest.raises(TypeError, match="Expected str"):
        clean_whitespace(None)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 3: ASCII TRANSLITERATION (normalize_ascii)
# ==============================================================================


@pytest.mark.unit
def test_normalize_ascii_decomposes_diacritics_cleanly() -> None:
    """Verify normalize_ascii decomposes accents into pure ASCII equivalents."""
    assert normalize_ascii("Müller") == "Muller"
    assert normalize_ascii("Renée") == "Renee"
    assert normalize_ascii("São Paulo") == "Sao Paulo"


@pytest.mark.regression
def test_normalize_ascii_non_string_raises_type_error() -> None:
    """Verify normalize_ascii raises TypeError on invalid types."""
    with pytest.raises(TypeError, match="Expected str"):
        normalize_ascii(100)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 4: SLUG GENERATION & URN PATHS (slugify)
# ==============================================================================


@pytest.mark.unit
def test_slugify_standard_uri_and_filesystem_mode() -> None:
    """Verify slugify generates lowercase hyphenated strings by default."""
    assert slugify("New Hampshire") == "new-hampshire"
    assert slugify("Saint-Jean-sur-Richelieu") == "saint-jean-sur-richelieu"
    assert slugify("  Rock & Roll!  ") == "rock-roll"


@pytest.mark.unit
def test_slugify_allow_colons_for_urn_paths() -> None:
    """Verify slugify preserves colons and custom delimiters when allow_colons is True."""
    result = slugify("urn:gda:loc:united states:nh", delimiter="_", allow_colons=True)
    assert result == "urn:gda:loc:united_states:nh"

    messy = ":::urn:gda:loc:state-name:sub district:::"
    cleaned = slugify(messy, delimiter="_", allow_colons=True)
    assert cleaned == "urn:gda:loc:state_name:sub_district"


@pytest.mark.regression
def test_slugify_non_string_raises_type_error() -> None:
    """Verify slugify raises TypeError on non-string inputs."""
    with pytest.raises(TypeError, match="Expected str"):
        slugify(None)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 5: PHONETIC ALGORITHMS (phonetic_soundex & phonetic_nysiis)
# ==============================================================================


@pytest.mark.unit
def test_phonetic_soundex_canonical_encodings() -> None:
    """Verify Soundex algorithm against standard genealogical names."""
    assert phonetic_soundex("Smith") == "S530"
    assert phonetic_soundex("Smythe") == "S530"
    assert phonetic_soundex("Pfister") == "P236"
    assert phonetic_soundex("12345") == "0000"
    assert phonetic_soundex("") == "0000"


@pytest.mark.regression
def test_phonetic_soundex_non_string_raises_type_error() -> None:
    """Verify phonetic_soundex raises TypeError on non-string inputs."""
    with pytest.raises(TypeError, match="Expected str"):
        phonetic_soundex(None)  # type: ignore[arg-type]


@pytest.mark.unit
def test_phonetic_nysiis_canonical_encodings() -> None:
    """Verify NYSIIS encoding across prefix and suffix rules."""
    assert phonetic_nysiis("MacDonald") == "MCDANALD"
    assert phonetic_nysiis("Knight") == "NAGT"
    assert phonetic_nysiis("Schmidt") == "SNAD"
    assert phonetic_nysiis("12345") == ""
    assert phonetic_nysiis("") == ""


@pytest.mark.regression
def test_phonetic_nysiis_non_string_raises_type_error() -> None:
    """Verify phonetic_nysiis raises TypeError on non-string inputs."""
    with pytest.raises(TypeError, match="Expected str"):
        phonetic_nysiis(None)  # type: ignore[arg-type]
