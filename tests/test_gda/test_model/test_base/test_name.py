# Name: test_name.py
# Path: tests/test_gda/test_model/test_base/test_name.py

"""Comprehensive test suite verifying CanonicalNameModel formatting and properties.

Operational Role:
    Verifies that CanonicalNameModel enforces non-empty raw_name invariants,
    constructs standardized full_name strings across present segments,
    supports maiden names and suffixes, and guarantees immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.model.atom.errors import AtomFormatError
from gda.model.base.name import CanonicalNameModel

__version__ = "1.0.0+build.r2"


# ==============================================================================
# GROUP 1: CANONICALNAMEMODEL CREATION & DISPLAY PROPERTIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_canonical_name_model_full_segments() -> None:
    """Verify CanonicalNameModel constructs full display name from all segments."""
    name = CanonicalNameModel(
        raw_name="Col. John Quincy Adams Jr.",
        given="John",
        middle="Quincy",
        surname="Adams",
        suffix="Jr.",
        maiden_name=None,
    )
    assert name.raw_name == "Col. John Quincy Adams Jr."
    assert name.given == "John"
    assert name.middle == "Quincy"
    assert name.surname == "Adams"
    assert name.suffix == "Jr."
    assert name.maiden_name is None
    assert name.full_name == "John Quincy Adams Jr."
    assert str(name) == "John Quincy Adams Jr."
    assert repr(name) == (
        "CanonicalNameModel(raw_name='Col. John Quincy Adams Jr.', "
        "given='John', middle='Quincy', surname='Adams', suffix='Jr.', maiden_name=None)"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_canonical_name_model_given_and_surname_only() -> None:
    """Verify CanonicalNameModel formats cleanly without middle or suffix."""
    name = CanonicalNameModel(
        raw_name="Mary Smith",
        given="Mary",
        surname="Smith",
        maiden_name="Jones",
    )
    assert name.full_name == "Mary Smith"
    assert name.maiden_name == "Jones"


@pytest.mark.unit
@pytest.mark.smoke
def test_canonical_name_model_raw_only_fallback() -> None:
    """Verify CanonicalNameModel falls back to raw_name when segments are absent."""
    name = CanonicalNameModel(raw_name="Widow Johnson")
    assert name.full_name == "Widow Johnson"
    assert str(name) == "Widow Johnson"


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & IMMUTABILITY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_name", ["", "   ", "\t\n"])
def test_canonical_name_empty_raw_name_raises_error(blank_name: str) -> None:
    """Verify CanonicalNameModel raises AtomFormatError if raw_name is empty."""
    with pytest.raises(AtomFormatError, match="raw_name cannot be empty"):
        CanonicalNameModel(raw_name=blank_name)


@pytest.mark.unit
def test_canonical_name_immutability() -> None:
    """Verify CanonicalNameModel is frozen and immutable."""
    name = CanonicalNameModel(raw_name="John Doe", given="John", surname="Doe")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        name.given = "Jane"  # type: ignore[misc]


@pytest.mark.unit
def test_canonical_name_introspection() -> None:
    """Verify .help() renders member directory on CanonicalNameModel."""
    name = CanonicalNameModel(raw_name="John Doe")
    help_text = name.help(as_str=True)
    assert help_text is not None
    assert "=== CanonicalNameModel Public Directory ===" in help_text
    assert "full_name" in help_text
