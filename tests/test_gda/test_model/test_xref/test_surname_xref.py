"""Path: tests/test_gda/test_model/test_xref/test_surname_xref.py

Comprehensive unit tests for gda.model.xref.surname_xref.SurnameXRef.

Operational Role:
    Exercises SurnameXRef creation for primary and historical/colloquial surname
    variants, bi-conditional HistoricNameType.PRIMARY equality invariants,
    phonetic code normalization, dynamic xref_key and sort_key ordering,
    dict/JSON round-trip serialization, and defensive validation boundaries.
"""

from __future__ import annotations

import pytest
from tests.test_gda.test_model.test_xref.conftest import assert_xref_contract

from gda.core.enums.vital import HistoricNameType
from gda.core.errors import ModelFormatError
from gda.model.xref import SurnameXRef

__version__ = "1.0.0+build.1"


@pytest.mark.unit
@pytest.mark.smoke
def test_surname_xref_primary_and_variants_roundtrip() -> None:
    """Verify SurnameXRef creation, normalization, dynamic keys, ordering, and serialization."""
    primary = SurnameXRef.create(
        canonical_surname="  abbott  ",
        variant_phonetic_code="  a130  ",
    )
    assert_xref_contract(primary, SurnameXRef)
    assert primary.canonical_surname == "ABBOTT"
    assert primary.variant_surname == "ABBOTT"
    assert primary.variant_name_type is HistoricNameType.PRIMARY
    assert primary.variant_phonetic_code == "A130"
    assert primary.is_canonical_self is True
    assert primary.xref_key == "ABBOTT::ABBOTT"
    assert primary.sort_key == ("ABBOTT", 0, "ABBOTT", "PRIMARY")
    assert str(primary) == "SurnameXRef [ABBOTT::ABBOTT] (PRIMARY) [A130]"
    assert "SurnameXRef(" in repr(primary)

    # Variant with default HISTORICAL type and no phonetic code
    variant_hist = SurnameXRef.create(
        canonical_surname="abbott",
        variant_surname="  abbot  ",
    )
    assert_xref_contract(variant_hist, SurnameXRef)
    assert variant_hist.canonical_surname == "ABBOTT"
    assert variant_hist.variant_surname == "ABBOT"
    assert variant_hist.variant_name_type is HistoricNameType.HISTORICAL
    assert variant_hist.variant_phonetic_code is None
    assert variant_hist.is_canonical_self is False
    assert variant_hist.xref_key == "ABBOTT::ABBOT"
    assert str(variant_hist) == "SurnameXRef [ABBOTT::ABBOT] (HISTORICAL)"
    assert "variant_phonetic_code" not in variant_hist.to_dict()

    # Variant with explicit string and enum HistoricNameType + direct dataclass normalization
    variant_colloq = SurnameXRef.create(
        canonical_surname="ABBOTT",
        variant_surname="ABBET",
        variant_name_type="  colloquial  ",
        variant_phonetic_code="A130",
    )
    assert variant_colloq.variant_name_type is HistoricNameType.COLLOQUIAL

    direct_norm = SurnameXRef(
        canonical_surname="  rolfe ",
        variant_surname=" rolph ",
        variant_name_type=HistoricNameType.COLONIAL,
        variant_phonetic_code=" r410 ",
    )
    assert direct_norm.canonical_surname == "ROLFE"
    assert direct_norm.variant_surname == "ROLPH"
    assert direct_norm.variant_phonetic_code == "R410"

    # Deterministic ordering: primary < variant_colloq ("ABBET") < variant_hist ("ABBOT") < direct_norm ("ROLFE")
    assert primary < variant_colloq < variant_hist < direct_norm


@pytest.mark.unit
@pytest.mark.integrity
def test_surname_xref_validation_errors() -> None:
    """Verify PRIMARY equality invariants and validation error branches for SurnameXRef."""
    with pytest.raises(ModelFormatError, match="cannot be empty or whitespace"):
        SurnameXRef.create(canonical_surname="   ")

    with pytest.raises(ModelFormatError, match="cannot be empty or whitespace"):
        SurnameXRef.create(canonical_surname="ABBOTT", variant_surname="   ")

    with pytest.raises(
        ModelFormatError, match="'variant_phonetic_code' cannot be empty or whitespace"
    ):
        SurnameXRef.create(
            canonical_surname="ABBOTT",
            variant_phonetic_code="   ",
        )

    with pytest.raises(
        ModelFormatError,
        match="variant_name_type=PRIMARY requires canonical_surname",
    ):
        SurnameXRef.create(
            canonical_surname="ABBOTT",
            variant_surname="ABBOT",
            variant_name_type=HistoricNameType.PRIMARY,
        )

    with pytest.raises(
        ModelFormatError,
        match="canonical_surname == variant_surname \\('ABBOTT'\\) must use variant_name_type=PRIMARY",
    ):
        SurnameXRef.create(
            canonical_surname="ABBOTT",
            variant_surname="ABBOTT",
            variant_name_type=HistoricNameType.HISTORICAL,
        )

    with pytest.raises(ModelFormatError, match="Invalid HistoricNameType value"):
        SurnameXRef.create(
            canonical_surname="ABBOTT",
            variant_surname="ABBOT",
            variant_name_type="INVALID_TYPE",
        )

    with pytest.raises(
        ModelFormatError, match="requires 'canonical_surname' and 'variant_surname'"
    ):
        SurnameXRef.from_dict({"canonical_surname": "ABBOTT"})
