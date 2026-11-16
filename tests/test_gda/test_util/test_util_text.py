"""Path: tests/test_gda/test_util/test_util_text.py

Comprehensive unit test suite for pure stateless text utilities.

Operational Role:
    Verifies string sanitization, whitespace cleansing, ASCII transliteration,
    filesystem/URI slugging, American Soundex, and canonical Taft (1970) NYSIIS
    phonetic algorithms with 100% statement and branch coverage.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Decorated with @pytest.mark.unit and @pytest.mark.smoke.
    - Dependencies: In-memory evaluation with zero disk I/O.
"""

from __future__ import annotations

import pytest

import gda.util.text as utext

__version__ = "1.0.0+build.5"


# ==============================================================================
# GROUP 1: STRING SANITIZATION & DELIMITER STRIPPING (clean_string)
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_clean_string_valid_strings_stripped_and_normalized() -> None:
    """Verify clean_string strips enclosing punctuation and normalizes separators."""
    assert utext.clean_string("  @#*John Doe*#@  ") == "John Doe"
    assert utext.clean_string("<<Jane_Doe>>") == "Jane Doe"
    assert utext.clean_string("Alice?Bob~Charlie") == "Alice Bob Charlie"
    assert utext.clean_string("   Clean Text   ") == "Clean Text"


@pytest.mark.regression
def test_clean_string_non_string_or_empty_returns_none() -> None:
    """Verify clean_string returns None for non-strings, pure whitespace, or delimiters."""
    assert utext.clean_string(None) is None
    assert utext.clean_string(12345) is None
    assert utext.clean_string([]) is None
    assert utext.clean_string("") is None
    assert utext.clean_string("     ") is None
    assert utext.clean_string("@#*\"'<>") is None
    assert utext.clean_string("___***???") is None


# ==============================================================================
# GROUP 2: WHITESPACE NORMALIZATION (clean_whitespace)
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
    raw = "Line 1   with   spaces\r\n\r\nLine 2\t\twith tabs\rLine 3\n"
    expected = "Line 1 with spaces\n\nLine 2 with tabs\nLine 3"
    assert utext.clean_whitespace(raw) == expected


@pytest.mark.unit
def test_clean_whitespace_empty_or_pure_whitespace_returns_empty() -> None:
    """Verify clean_whitespace returns empty string for blank text."""
    assert utext.clean_whitespace("   \t\n\r   ") == ""
    assert utext.clean_whitespace("") == ""


@pytest.mark.regression
def test_clean_whitespace_non_string_raises_type_error() -> None:
    """Verify clean_whitespace rejects non-string inputs with TypeError."""
    with pytest.raises(TypeError, match="Expected str"):
        utext.clean_whitespace(None)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 3: ASCII TRANSLITERATION (normalize_ascii)
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_normalize_ascii_decomposes_diacritics_cleanly() -> None:
    """Verify normalize_ascii decomposes accents into pure ASCII equivalents."""
    raw = "Müller, François, Ångström, and Peña"
    assert utext.normalize_ascii(raw) == "Muller, Francois, Angstrom, and Pena"


@pytest.mark.unit
def test_normalize_ascii_drops_non_latin_characters() -> None:
    """Verify normalize_ascii drops Unicode glyphs that have no ASCII equivalents."""
    raw = "Name: 姓名 (Test)"
    assert utext.normalize_ascii(raw) == "Name:  (Test)"


@pytest.mark.regression
def test_normalize_ascii_non_string_raises_type_error() -> None:
    """Verify normalize_ascii raises TypeError on invalid types."""
    with pytest.raises(TypeError, match="Expected str"):
        utext.normalize_ascii(None)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 4: SLUG GENERATION & URN PATHS (slugify)
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_slugify_standard_uri_and_filesystem_mode() -> None:
    """Verify slugify generates lowercase hyphenated strings by default."""
    assert utext.slugify("New Hampshire") == "new-hampshire"
    assert utext.slugify("Saint-Jean-sur-Richelieu") == "saint-jean-sur-richelieu"
    assert utext.slugify("  Rock & Roll!  ") == "rock-roll"


@pytest.mark.unit
def test_slugify_respects_custom_delimiter() -> None:
    """Verify slugify uses an alternative delimiter when supplied."""
    raw = "Document Ingestion 1910"
    assert utext.slugify(raw, delimiter="_") == "document_ingestion_1910"


@pytest.mark.unit
def test_slugify_allow_colons_for_urn_paths() -> None:
    """Verify slugify preserves colons and custom delimiters when allow_colons is True."""
    result = utext.slugify("urn:gda:loc:united states:nh", delimiter="_", allow_colons=True)
    assert result == "urn:gda:loc:united_states:nh"

    messy = ":::urn:gda:loc:state-name:sub district:::"
    cleaned = utext.slugify(messy, delimiter="_", allow_colons=True)
    assert cleaned == "urn:gda:loc:state_name:sub_district"


@pytest.mark.unit
def test_slugify_handles_empty_or_non_alphanumeric_strings() -> None:
    """Verify slugify returns an empty string when no alphanumeric characters exist."""
    assert utext.slugify("---!@#$%^---") == ""
    assert utext.slugify("") == ""


@pytest.mark.regression
def test_slugify_non_string_raises_type_error() -> None:
    """Verify slugify raises TypeError on non-string inputs."""
    with pytest.raises(TypeError, match="Expected str"):
        utext.slugify(None)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 5: AMERICAN SOUNDEX PHONETIC ENCODING (phonetic_soundex)
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_phonetic_soundex_encodes_standard_surnames() -> None:
    """Verify Soundex algorithm against standard genealogical names."""
    assert utext.phonetic_soundex("Smith") == "S530"
    assert utext.phonetic_soundex("Smythe") == "S530"
    assert utext.phonetic_soundex("Robert") == "R163"
    assert utext.phonetic_soundex("Rupert") == "R163"
    assert utext.phonetic_soundex("Ashcraft") == "A261"
    assert utext.phonetic_soundex("Pfister") == "P236"


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


@pytest.mark.regression
def test_phonetic_soundex_non_string_raises_type_error() -> None:
    """Verify phonetic_soundex raises TypeError on non-string inputs."""
    with pytest.raises(TypeError, match="Expected str"):
        utext.phonetic_soundex(None)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 6: CANONICAL NYSIIS PHONETIC ALGORITHM (phonetic_nysiis)
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_phonetic_nysiis_canonical_historical_surnames() -> None:
    """Verify NYSIIS encoding across standard genealogical surname baselines."""
    assert utext.phonetic_nysiis("Smith") == "SNAT"
    assert utext.phonetic_nysiis("Schmidt") == "SNAD"
    assert utext.phonetic_nysiis("MacDonald") == "MCDANALD"
    assert utext.phonetic_nysiis("Knight") == "NAGT"
    assert utext.phonetic_nysiis("Pfeiffer") == "FAFAR"
    assert utext.phonetic_nysiis("White") == "WAT"
    assert utext.phonetic_nysiis("Brown") == "BRAN"
    assert utext.phonetic_nysiis("Kelly") == "CALY"


@pytest.mark.unit
def test_phonetic_nysiis_handles_empty_or_non_alpha_inputs() -> None:
    """Verify phonetic_nysiis returns an empty string when given non-alphabetic inputs."""
    assert utext.phonetic_nysiis("") == ""
    assert utext.phonetic_nysiis("12345") == ""
    assert utext.phonetic_nysiis("@#$%") == ""


@pytest.mark.regression
def test_phonetic_nysiis_raises_type_error_for_non_string() -> None:
    """Verify phonetic_nysiis raises TypeError when passed non-string inputs."""
    with pytest.raises(TypeError, match="Expected str"):
        utext.phonetic_nysiis(None)  # type: ignore[arg-type]


@pytest.mark.unit
def test_phonetic_nysiis_single_character_tokens() -> None:
    """Verify phonetic_nysiis handles single vowel and single consonant tokens."""
    assert utext.phonetic_nysiis("A") == "A"
    assert utext.phonetic_nysiis("K") == "C"


@pytest.mark.unit
def test_phonetic_nysiis_initial_consonant_runs() -> None:
    """Verify phonetic_nysiis initial duplicate runs and collapsing."""
    assert utext.phonetic_nysiis("David") == "DAVAD"
    assert utext.phonetic_nysiis("Lloyd") == "LAYD"
    assert utext.phonetic_nysiis("BBB") == "B"


@pytest.mark.unit
def test_phonetic_nysiis_prefix_rules() -> None:
    """Verify phonetic_nysiis initial prefix rules (K, PH, SCH)."""
    assert utext.phonetic_nysiis("Kemp") == "CANP"
    assert utext.phonetic_nysiis("Philip") == "FALAP"


@pytest.mark.unit
def test_phonetic_nysiis_suffix_rules() -> None:
    """Verify phonetic_nysiis terminal suffix reductions (EE, IE, DT, RD, NT, ND, AY, S, A)."""
    assert utext.phonetic_nysiis("McKee") == "MCY"
    assert utext.phonetic_nysiis("Carlie") == "CARLY"
    assert utext.phonetic_nysiis("Ford") == "FAD"
    assert utext.phonetic_nysiis("Grant") == "GRAD"
    assert utext.phonetic_nysiis("Bond") == "BAD"
    assert utext.phonetic_nysiis("Clay") == "CLY"
    assert utext.phonetic_nysiis("Williams") == "WALAN"
    assert utext.phonetic_nysiis("Spann") == "SPAN"


@pytest.mark.unit
def test_phonetic_nysiis_internal_consonant_and_digraph_rules() -> None:
    """Verify internal NYSIIS digraph and consonant transformations."""
    # EV -> AF
    assert utext.phonetic_nysiis("Trevor") == "TRAFAR"
    # Q -> G
    assert utext.phonetic_nysiis("McQuinn") == "MCGAN"
    # Z -> S
    assert utext.phonetic_nysiis("Hazard") == "HASAD"
    # M/P/B and M -> N
    assert utext.phonetic_nysiis("Campbell") == "CANBAL"
    # KN -> N
    assert utext.phonetic_nysiis("Buckner") == "BACNAR"
    # K -> C
    assert utext.phonetic_nysiis("Baker") == "BACAR"
    assert utext.phonetic_nysiis("Blackwood") == "BLACWAD"
    assert utext.phonetic_nysiis("Mark") == "MARC"
    # SCH -> S
    assert utext.phonetic_nysiis("Riesch") == "RAS"
    # PH -> FF -> F
    assert utext.phonetic_nysiis("Joseph") == "JASAF"
    # H and W dropping rules
    assert utext.phonetic_nysiis("Rhodes") == "RAD"
    assert utext.phonetic_nysiis("Abraham") == "ABRAHAN"
    assert utext.phonetic_nysiis("Bowman") == "BANAN"
