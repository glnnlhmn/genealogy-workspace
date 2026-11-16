"""Path: tests/test_gda/test_model/test_xref/test_individual_surname_xref.py

Comprehensive unit tests for gda.model.xref.individual_surname_xref.IndividualSurnameXRef.

Operational Role:
    Exercises IndividualSurnameXRef creation, uppercase surname normalization,
    BirthYear and DeathYear integration and lifespan range validation,
    IndividualSurnameXRef.from_individual() derivation, dynamic xref_key and
    sort_key ordering, dict/JSON round-trip serialization, and defensive
    validation boundaries.
"""

from __future__ import annotations

import pytest
from tests.test_gda.test_model.test_xref.conftest import assert_xref_contract

from gda.core.errors import ModelFormatError, ModelPrefixMismatchError, ModelRangeError
from gda.model.atom.id import IndividualID
from gda.model.atom.year import BirthYear, DeathYear
from gda.model.base.name import NamePerson
from gda.model.entity.individual import Individual
from gda.model.xref import IndividualSurnameXRef

__version__ = "1.0.0+build.3"


@pytest.mark.unit
@pytest.mark.smoke
def test_individual_surname_xref_roundtrip_and_ordering(
    sample_individual_id: IndividualID,
    sample_birth_year: BirthYear,
    sample_death_year: DeathYear,
) -> None:
    """Verify IndividualSurnameXRef creation, normalization, keys, ordering, and serialization."""
    birth_xref = IndividualSurnameXRef.create(
        surname="  abbott  ",
        individual_id="  ind-000010  ",
        is_birth_surname=True,
        birth_year=1844,
        death_year=1912,
    )
    assert_xref_contract(birth_xref, IndividualSurnameXRef)
    assert birth_xref.surname == "ABBOTT"
    assert birth_xref.individual_id == sample_individual_id
    assert birth_xref.is_birth_surname is True
    assert birth_xref.birth_year == sample_birth_year
    assert birth_xref.death_year == sample_death_year
    assert birth_xref.role_label == "BIRTH"
    assert birth_xref.xref_key == "ABBOTT::IND-000010::BIRTH"
    assert birth_xref.sort_key == ("ABBOTT", 1844, 1912, 0, "IND-000010")
    assert str(birth_xref) == "IndividualSurnameXRef [ABBOTT::IND-000010::BIRTH] (1844-1912)"
    assert "IndividualSurnameXRef(" in repr(birth_xref)

    # Married surname with direct atom instances & direct constructor normalization
    married_xref = IndividualSurnameXRef(
        surname="  rolfe ",
        individual_id=sample_individual_id,
        is_birth_surname=False,
        birth_year=sample_birth_year,
    )
    assert_xref_contract(married_xref, IndividualSurnameXRef)
    assert married_xref.surname == "ROLFE"
    assert married_xref.is_birth_surname is False
    assert married_xref.role_label == "OTHER"
    assert married_xref.xref_key == "ROLFE::IND-000010::OTHER"
    assert str(married_xref) == "IndividualSurnameXRef [ROLFE::IND-000010::OTHER] (1844-?)"

    # Undated minimal instance
    undated = IndividualSurnameXRef.create(
        surname="ABBOTT",
        individual_id="IND-000020",
        is_birth_surname=False,
    )
    assert str(undated) == "IndividualSurnameXRef [ABBOTT::IND-000020::OTHER]"
    assert "birth_year" not in undated.to_dict()
    assert "death_year" not in undated.to_dict()
    assert IndividualSurnameXRef.from_dict(undated.to_dict()) == undated

    # Death-only span formatting
    death_only = IndividualSurnameXRef.create(
        surname="ABBOTT",
        individual_id=sample_individual_id,
        death_year=sample_death_year,
    )
    assert str(death_only) == "IndividualSurnameXRef [ABBOTT::IND-000010::BIRTH] (?-1912)"

    # Deterministic ordering: birth_xref (1844) < death_only (birth=9999, death=1912) < undated < married_xref ("ROLFE")
    assert birth_xref < death_only < undated < married_xref


@pytest.mark.unit
@pytest.mark.integrity
def test_individual_surname_xref_from_individual_derivation() -> None:
    """Verify IndividualSurnameXRef.from_individual() for birth, married, and mononymous individuals."""
    person = Individual.create(
        individual_id="IND-000002",
        name=NamePerson.create(
            raw="Mary Elizabeth Rolfe",
            given="Mary Elizabeth",
            surname="Rolfe",
            married=["Abbott", "Smith"],
        ),
        canonical_urn="urn:gda:ind:rolfe_mary_1848",
        gender="F",
        birth_date="1848-03-10",
        death_date="1920-11-04",
    )

    rows = IndividualSurnameXRef.from_individual(person)
    assert len(rows) == 3
    assert rows[0].surname == "ROLFE"
    assert rows[0].is_birth_surname is True
    assert rows[0].birth_year == BirthYear(1848)
    assert rows[0].death_year == DeathYear(1920)

    assert rows[1].surname == "ABBOTT"
    assert rows[1].is_birth_surname is False
    assert rows[2].surname == "SMITH"
    assert rows[2].is_birth_surname is False

    # Individual with no birth surname (surname=None) and married surname only
    mononymous = Individual.create(
        individual_id="IND-000003",
        name=NamePerson(
            raw="Elizabeth",
            canonical="Elizabeth",
            given="Elizabeth",
            surname=None,
            married=["Abbott"],
        ),
        canonical_urn="urn:gda:ind:elizabeth_unknown",
    )
    mono_rows = IndividualSurnameXRef.from_individual(mononymous)
    assert len(mono_rows) == 1
    assert mono_rows[0].surname == "ABBOTT"
    assert mono_rows[0].is_birth_surname is False
    assert mono_rows[0].birth_year is None
    assert mono_rows[0].death_year is None

    with pytest.raises(ModelFormatError, match="requires an Individual entity instance"):
        IndividualSurnameXRef.from_individual("not-an-individual")  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.integrity
def test_individual_surname_xref_validation_errors() -> None:
    """Verify lifespan range and format validation error branches for IndividualSurnameXRef."""
    with pytest.raises(ModelFormatError, match="cannot be empty or whitespace"):
        IndividualSurnameXRef.create(surname="   ", individual_id="IND-000001")

    with pytest.raises(ModelPrefixMismatchError, match="expected 'IND'"):
        IndividualSurnameXRef.create(surname="ABBOTT", individual_id="FAM-000001")

    with pytest.raises(
        ModelRangeError,
        match="Death year \\(1840\\) cannot precede birth year \\(1850\\)",
    ):
        IndividualSurnameXRef.create(
            surname="ABBOTT",
            individual_id="IND-000001",
            birth_year=1850,
            death_year=1840,
        )

    with pytest.raises(ModelRangeError):
        IndividualSurnameXRef.create(
            surname="ABBOTT",
            individual_id="IND-000001",
            birth_year=999,
        )

    with pytest.raises(ModelFormatError, match="requires 'surname', 'individual_id'"):
        IndividualSurnameXRef.from_dict({"surname": "ABBOTT"})
