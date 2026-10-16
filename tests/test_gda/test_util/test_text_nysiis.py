# Name: test_text_nysiis.py
# Path: tests/test_gda/test_util/test_text_nysiis.py

"""Comprehensive unit test suite for NYSIIS phonetic transformation in gda.util.text.

Operational Role:
    Verifies Refined NYSIIS phonetic transformation against canonical Taft (1970)
    invariants, prefix/suffix reduction rules, and isolated internal digraph branches.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Decorated with @pytest.mark.unit and @pytest.mark.smoke.
    - Dependencies: In-memory evaluation with zero disk I/O.

Note:
    PRERELEASE: Test suite is under active development (version 0.0.1+build.r10).
"""

from __future__ import annotations

__version__ = "0.0.1+build.r10"

import pytest

import gda.util.text as utext

# ==============================================================================
# GROUP 1: Canonical Historical Surnames & Invariant Baselines
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_phonetic_nysiis_encodes_smith() -> None:
    """Verify phonetic_nysiis encodes Smith to SNAT."""
    assert utext.phonetic_nysiis("Smith") == "SNAT"


@pytest.mark.unit
def test_phonetic_nysiis_encodes_schmidt() -> None:
    """Verify phonetic_nysiis encodes Schmidt to SNAD."""
    assert utext.phonetic_nysiis("Schmidt") == "SNAD"


@pytest.mark.unit
def test_phonetic_nysiis_encodes_macdonald() -> None:
    """Verify phonetic_nysiis encodes MacDonald to MCDANALD."""
    assert utext.phonetic_nysiis("MacDonald") == "MCDANALD"


@pytest.mark.unit
def test_phonetic_nysiis_encodes_knight() -> None:
    """Verify phonetic_nysiis encodes Knight to NAGT."""
    assert utext.phonetic_nysiis("Knight") == "NAGT"


@pytest.mark.unit
def test_phonetic_nysiis_encodes_pfeiffer() -> None:
    """Verify phonetic_nysiis encodes Pfeiffer to FAFAR."""
    assert utext.phonetic_nysiis("Pfeiffer") == "FAFAR"


@pytest.mark.unit
def test_phonetic_nysiis_encodes_white() -> None:
    """Verify phonetic_nysiis encodes White to WAT."""
    assert utext.phonetic_nysiis("White") == "WAT"


@pytest.mark.unit
def test_phonetic_nysiis_encodes_brown() -> None:
    """Verify phonetic_nysiis encodes Brown to BRAN."""
    assert utext.phonetic_nysiis("Brown") == "BRAN"


@pytest.mark.unit
def test_phonetic_nysiis_encodes_kelly() -> None:
    """Verify phonetic_nysiis encodes Kelly to CALY."""
    assert utext.phonetic_nysiis("Kelly") == "CALY"


# ==============================================================================
# GROUP 2: Defensive Boundaries & Invalid Types
# ==============================================================================


@pytest.mark.unit
def test_phonetic_nysiis_handles_empty_or_non_alpha_inputs() -> None:
    """Verify phonetic_nysiis returns an empty string when given non-alphabetic inputs."""
    assert utext.phonetic_nysiis("") == ""
    assert utext.phonetic_nysiis("12345") == ""
    assert utext.phonetic_nysiis("@#$%") == ""


@pytest.mark.unit
def test_phonetic_nysiis_raises_type_error_for_non_string() -> None:
    """Verify phonetic_nysiis raises TypeError when passed non-string inputs."""
    with pytest.raises(TypeError, match="Expected str"):
        utext.phonetic_nysiis(b"Smith")  # type: ignore[arg-type]


@pytest.mark.unit
def test_phonetic_nysiis_handles_single_vowel_token() -> None:
    """Verify phonetic_nysiis preserves single vowel tokens without length collapse."""
    assert utext.phonetic_nysiis("A") == "A"


@pytest.mark.unit
def test_phonetic_nysiis_handles_single_character_consonant() -> None:
    """Verify phonetic_nysiis preserves single-letter non-vowel consonant strings."""
    assert utext.phonetic_nysiis("K") == "C"


@pytest.mark.unit
def test_phonetic_nysiis_handles_distinct_second_character() -> None:
    """Verify phonetic_nysiis bypasses initial duplication loop when second char differs."""
    assert utext.phonetic_nysiis("David") == "DAVAD"


@pytest.mark.unit
def test_phonetic_nysiis_handles_repeated_initial_consonants() -> None:
    """Verify phonetic_nysiis collapses repeated initial consonants."""
    assert utext.phonetic_nysiis("Lloyd") == "LAYD"


@pytest.mark.unit
def test_phonetic_nysiis_handles_repeated_initial_run_until_end() -> None:
    """Verify phonetic_nysiis terminates when entire string is an identical repeating run."""
    assert utext.phonetic_nysiis("BBB") == "B"


# ==============================================================================
# GROUP 3: Prefix & Suffix Transformation Rules
# ==============================================================================


@pytest.mark.unit
def test_phonetic_nysiis_prefix_k_maps_to_c() -> None:
    """Verify phonetic_nysiis translates initial K to C."""
    assert utext.phonetic_nysiis("Kemp") == "CANP"


@pytest.mark.unit
def test_phonetic_nysiis_prefix_ph_maps_to_ff() -> None:
    """Verify phonetic_nysiis translates initial PH to FF."""
    assert utext.phonetic_nysiis("Philip") == "FALAP"


@pytest.mark.unit
def test_phonetic_nysiis_suffix_ee_maps_to_y() -> None:
    """Verify phonetic_nysiis reduces terminal EE to Y."""
    assert utext.phonetic_nysiis("McKee") == "MCY"


@pytest.mark.unit
def test_phonetic_nysiis_suffix_ie_maps_to_y() -> None:
    """Verify phonetic_nysiis reduces terminal IE to Y."""
    assert utext.phonetic_nysiis("Carlie") == "CARLY"


@pytest.mark.unit
def test_phonetic_nysiis_suffix_dt_maps_to_d() -> None:
    """Verify phonetic_nysiis reduces terminal DT to D."""
    assert utext.phonetic_nysiis("Schmidt") == "SNAD"


@pytest.mark.unit
def test_phonetic_nysiis_suffix_rd_maps_to_d() -> None:
    """Verify phonetic_nysiis reduces terminal RD to D."""
    assert utext.phonetic_nysiis("Ford") == "FAD"


@pytest.mark.unit
def test_phonetic_nysiis_suffix_nt_maps_to_d() -> None:
    """Verify phonetic_nysiis reduces terminal NT to D."""
    assert utext.phonetic_nysiis("Grant") == "GRAD"


@pytest.mark.unit
def test_phonetic_nysiis_suffix_nd_maps_to_d() -> None:
    """Verify phonetic_nysiis reduces terminal ND to D."""
    assert utext.phonetic_nysiis("Bond") == "BAD"


@pytest.mark.unit
def test_phonetic_nysiis_suffix_ay_maps_to_y() -> None:
    """Verify phonetic_nysiis reduces terminal AY to Y."""
    assert utext.phonetic_nysiis("Clay") == "CLY"


@pytest.mark.unit
def test_phonetic_nysiis_terminal_s_is_removed() -> None:
    """Verify phonetic_nysiis strips terminal S when key length exceeds 1."""
    assert utext.phonetic_nysiis("Williams") == "WALAN"


@pytest.mark.unit
def test_phonetic_nysiis_terminal_a_stripped_when_multichar() -> None:
    """Verify phonetic_nysiis strips terminal A on multicharacter keys."""
    assert utext.phonetic_nysiis("Spann") == "SPAN"


# ==============================================================================
# GROUP 4: Atomized Internal Digraph & Consonant Rules
# ==============================================================================


@pytest.mark.unit
def test_phonetic_nysiis_internal_ev_maps_to_af() -> None:
    """Verify phonetic_nysiis converts internal EV to AF."""
    assert utext.phonetic_nysiis("Trevor") == "TRAFAR"


@pytest.mark.unit
def test_phonetic_nysiis_internal_q_maps_to_g() -> None:
    """Verify phonetic_nysiis converts internal Q to G."""
    assert utext.phonetic_nysiis("McQuinn") == "MCGAN"


@pytest.mark.unit
def test_phonetic_nysiis_internal_z_maps_to_s() -> None:
    """Verify phonetic_nysiis converts internal Z to S."""
    assert utext.phonetic_nysiis("Hazard") == "HASAD"


@pytest.mark.unit
def test_phonetic_nysiis_internal_m_maps_to_n() -> None:
    """Verify phonetic_nysiis converts internal M to N and collapses MPB."""
    assert utext.phonetic_nysiis("Campbell") == "CANBAL"


@pytest.mark.unit
def test_phonetic_nysiis_internal_kn_maps_to_n() -> None:
    """Verify phonetic_nysiis converts internal KN to N."""
    assert utext.phonetic_nysiis("Buckner") == "BACNAR"


@pytest.mark.unit
def test_phonetic_nysiis_internal_k_maps_to_c() -> None:
    """Verify phonetic_nysiis converts internal K to C."""
    assert utext.phonetic_nysiis("Baker") == "BACAR"


@pytest.mark.unit
def test_phonetic_nysiis_internal_k_not_followed_by_n() -> None:
    """Verify phonetic_nysiis handles internal K when followed by a non-N character."""
    assert utext.phonetic_nysiis("Blackwood") == "BLACWAD"


@pytest.mark.unit
def test_phonetic_nysiis_internal_k_at_terminal_boundary() -> None:
    """Verify phonetic_nysiis handles K at the terminal position where nxt is empty."""
    assert utext.phonetic_nysiis("Mark") == "MARC"


@pytest.mark.unit
def test_phonetic_nysiis_internal_sch_maps_to_s() -> None:
    """Verify phonetic_nysiis converts internal SCH to S and preserves terminal S from SCH."""
    assert utext.phonetic_nysiis("Riesch") == "RAS"


@pytest.mark.unit
def test_phonetic_nysiis_internal_ph_maps_to_ff_deduplicated() -> None:
    """Verify phonetic_nysiis converts internal PH to F."""
    assert utext.phonetic_nysiis("Joseph") == "JASAF"


@pytest.mark.unit
def test_phonetic_nysiis_internal_h_drops_between_non_vowels() -> None:
    """Verify phonetic_nysiis drops H unless preceded and followed by vowels."""
    assert utext.phonetic_nysiis("Rhodes") == "RAD"
    assert utext.phonetic_nysiis("Abraham") == "ABRAHAN"


@pytest.mark.unit
def test_phonetic_nysiis_internal_w_drops_after_vowels() -> None:
    """Verify phonetic_nysiis drops W when preceded by a vowel."""
    assert utext.phonetic_nysiis("Bowman") == "BANAN"
