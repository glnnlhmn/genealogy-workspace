"""Path: tests/test_gda/test_model/test_base/test_source_reference.py

Comprehensive test suite verifying SourceReference contracts.

Operational Role:
    Verifies that SourceReference validates non-empty citations,
    binds optional SourceID, page, QuayScore, and ConfidenceScore attributes,
    formats string representations, and enforces immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.id import SourceID
from gda.model.atom.scalar import ConfidenceScore, QuayScore
from gda.model.base.source_reference import SourceReference

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: SOURCEREFERENCE CREATION & FORMATTING
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_source_reference_valid_creation() -> None:
    """Verify SourceReference instantiates with full and partial attributes."""
    sid = SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")
    quay = QuayScore(3)
    conf = ConfidenceScore(0.95)

    ref = SourceReference(
        citation_text="1880 US Census, Merrimack County, NH",
        source_id=sid,
        page_or_side="Folio 12B",
        quay=quay,
        confidence=conf,
    )
    assert ref.citation_text == "1880 US Census, Merrimack County, NH"
    assert ref.source_id == sid
    assert ref.page_or_side == "Folio 12B"
    assert ref.quay == quay
    assert ref.confidence == conf
    assert str(ref) == "1880 US Census, Merrimack County, NH (p. Folio 12B)"
    assert repr(ref) == (
        "SourceReference(citation_text='1880 US Census, Merrimack County, NH', "
        "source_id=SourceID(value='c9a646d3-9c61-4a70-8b14-c48c8b417c8d'), "
        "page_or_side='Folio 12B', quay=QuayScore(value=3), confidence=ConfidenceScore(value=0.95))"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_source_reference_unadorned_string_formatting() -> None:
    """Verify SourceReference string without page_or_side."""
    ref = SourceReference(citation_text="Family Bible Records")
    assert str(ref) == "Family Bible Records"
    assert ref.source_id is None
    assert ref.page_or_side is None


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & IMMUTABILITY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_citation", ["", "   ", "\t\n"])
def test_source_reference_blank_citation_raises_error(blank_citation: str) -> None:
    """Verify SourceReference raises ModelFormatError on empty citation_text."""
    with pytest.raises(ModelFormatError, match="citation_text cannot be empty"):
        SourceReference(citation_text=blank_citation)


@pytest.mark.unit
def test_source_reference_immutability() -> None:
    """Verify SourceReference is frozen and immutable."""
    ref = SourceReference(citation_text="Original Record")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        ref.citation_text = "Mutated Record"  # type: ignore[misc]


@pytest.mark.unit
def test_source_reference_introspection() -> None:
    """Verify .help() renders member directory on SourceReference."""
    ref = SourceReference(citation_text="Archive Memo")
    help_text = ref.help(as_str=True)
    assert help_text is not None
    assert "=== SourceReference Public Directory ===" in help_text
