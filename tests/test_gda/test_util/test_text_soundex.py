# Name: test_text_soundex.py
# Path: tests/test_gda/test_util/test_text_soundex.py

"""Comprehensive unit test suite for Soundex phonetic encoding in gda.util.text.

Operational Role:
    Verifies American Soundex phonetic encoding against historical US census
    invariants, zero-padding rules, and H/W separator invariants.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Decorated with @pytest.mark.unit and @pytest.mark.smoke.
    - Dependencies: In-memory evaluation with zero disk I/O.

Note:
    PRERELEASE: Test suite is under active development (version 0.0.1+build.r2).
"""

from __future__ import annotations

__version__ = "0.0.1+build.r2"

import pytest

import gda.util.text as utext

# ==============================================================================
# GROUP 4: American Soundex Phonetic Encoding
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_phonetic_soundex_encodes_standard_surnames() -> None:
    """Verify phonetic_soundex matches historical US census Soundex codes."""
    assert utext.phonetic_soundex("Smith") == "S530"
    assert utext.phonetic_soundex("Smythe") == "S530"
    assert utext.phonetic_soundex("Robert") == "R163"
    assert utext.phonetic_soundex("Rupert") == "R163"
    assert utext.phonetic_soundex("Ashcraft") == "A261"


@pytest.mark.unit
def test_phonetic_soundex_handles_short_names_and_padding() -> None:
    """Verify phonetic_soundex zero-pads names with fewer than three encoded consonants."""
    assert utext.phonetic_soundex("Lee") == "L000"
    assert utext.phonetic_soundex("Cox") == "C200"


@pytest.mark.unit
def test_phonetic_soundex_handles_empty_or_non_alpha_inputs() -> None:
    """Verify phonetic_soundex returns '0000' when no alphabetic characters are present."""
    assert utext.phonetic_soundex("") == "0000"
    assert utext.phonetic_soundex("12345") == "0000"
    assert utext.phonetic_soundex("---") == "0000"


@pytest.mark.unit
def test_phonetic_soundex_ignores_h_and_w() -> None:
    """Verify phonetic_soundex ignores H and W without resetting previous consonant code."""
    assert utext.phonetic_soundex("Hugh") == "H200"
    assert utext.phonetic_soundex("Bowman") == "B550"


@pytest.mark.unit
def test_phonetic_soundex_raises_type_error_for_non_string() -> None:
    """Verify phonetic_soundex raises TypeError when passed non-string inputs."""
    with pytest.raises(TypeError, match="Expected str"):
        utext.phonetic_soundex(None)  # type: ignore[arg-type]
