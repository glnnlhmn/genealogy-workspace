# Name: test_text_normalization.py
# Path: tests/test_gda/test_util/test_text_normalization.py

"""Comprehensive unit test suite for text normalization and slugging in gda.util.text.

Operational Role:
    Verifies pure stateless string manipulation, whitespace cleansing, ASCII
    transliteration, and URI/filesystem slugging.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Decorated with @pytest.mark.unit and @pytest.mark.smoke.
    - Dependencies: In-memory evaluation with zero disk I/O.

Note:
    PRERELEASE: Test suite is under active development (version 0.0.1+build.r1).
"""

from __future__ import annotations

import pytest

import gda.util.text as utext

__version__ = "0.0.1+build.r1"

# ==============================================================================
# GROUP 1: Whitespace Cleansing & Normalization
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_clean_whitespace_collapses_horizontal_whitespace() -> None:
    """Verify clean_whitespace collapses internal runs of spaces and tabs into a single space."""
    raw = "  John   \t  William   Smith  "
    assert utext.clean_whitespace(raw) == "John William Smith"


@pytest.mark.unit
def test_clean_whitespace_normalizes_crlf_and_cr_linebreaks() -> None:
    """Verify clean_whitespace normalizes Windows CRLF and classic Mac CR linebreaks."""
    raw = "Line 1\r\nLine 2\rLine 3\n"
    assert utext.clean_whitespace(raw) == "Line 1\nLine 2\nLine 3"


@pytest.mark.unit
def test_clean_whitespace_raises_type_error_for_non_string() -> None:
    """Verify clean_whitespace raises TypeError when passed non-string inputs."""
    with pytest.raises(TypeError, match="Expected str"):
        utext.clean_whitespace(12345)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 2: ASCII Transliteration & Diacritic Stripping
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_normalize_ascii_strips_combining_diacritics() -> None:
    """Verify normalize_ascii converts accented Latin glyphs into standard ASCII letters."""
    raw = "Müller, François, Ångström, and Peña"
    assert utext.normalize_ascii(raw) == "Muller, Francois, Angstrom, and Pena"


@pytest.mark.unit
def test_normalize_ascii_drops_non_latin_characters() -> None:
    """Verify normalize_ascii drops Unicode glyphs that have no ASCII equivalents."""
    raw = "Name: 姓名 (Test)"
    assert utext.normalize_ascii(raw) == "Name:  (Test)"


@pytest.mark.unit
def test_normalize_ascii_raises_type_error_for_non_string() -> None:
    """Verify normalize_ascii raises TypeError when passed non-string inputs."""
    with pytest.raises(TypeError, match="Expected str"):
        utext.normalize_ascii(None)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 3: Slug Generation
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_slugify_converts_mixed_casing_and_punctuation() -> None:
    """Verify slugify produces a clean lowercase delimiter-separated slug."""
    raw = "John 'Jack' O'Connor, Jr."
    assert utext.slugify(raw) == "john-jack-o-connor-jr"


@pytest.mark.unit
def test_slugify_respects_custom_delimiter() -> None:
    """Verify slugify uses an alternative delimiter when supplied."""
    raw = "Document Ingestion 1910"
    assert utext.slugify(raw, delimiter="_") == "document_ingestion_1910"


@pytest.mark.unit
def test_slugify_handles_empty_or_non_alphanumeric_strings() -> None:
    """Verify slugify returns an empty string when no alphanumeric characters exist."""
    assert utext.slugify("---!@#$%^---") == ""
    assert utext.slugify("") == ""


@pytest.mark.unit
def test_slugify_raises_type_error_for_non_string() -> None:
    """Verify slugify raises TypeError when passed non-string inputs."""
    with pytest.raises(TypeError, match="Expected str"):
        utext.slugify(42)  # type: ignore[arg-type]
