"""Path: tests/test_gda/test_model/test_base/test_composites/test_name.py

Comprehensive test suite verifying NameBase, NamePerson, NameThing, and HistoricVariant.

Operational Role:
    Verifies that NameBase establishes foundational noun invariants, NamePerson formats
    discrete personal onomastic parts with prefix, suffix, and married names, and NameThing
    manages multi-phase HistoricVariant collections with temporal bounding. Equips all
    models with copy-on-write mutators, tests multilingual Unicode and non-English edge cases,
    and validates dictionary and JSON serialization round-trips with 100% branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from gda.core.enums.vital import HistoricNameType
from gda.core.errors import ModelFormatError
from gda.model.base.date import TimePeriod
from gda.model.base.name import (
    CanonicalName,
    HistoricalName,
    HistoricVariant,
    NameBase,
    NamePerson,
    NameThing,
)

__version__ = "1.2.0+build.4"


# ==============================================================================
# GROUP 1: NAMEBASE INVARIANTS & BOUNDARIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_text", ["", " ", "\t\n"])
def test_name_base_blank_raw_and_canonical_raise_error(blank_text: str) -> None:
    """Verify NameBase raises ModelFormatError if raw or canonical is empty or whitespace."""
    with pytest.raises(ModelFormatError, match="'raw' cannot be empty"):
        NamePerson(raw=blank_text, canonical="Valid Canonical")

    with pytest.raises(ModelFormatError, match="'canonical' cannot be empty"):
        NamePerson(raw="Valid Raw", canonical=blank_text)


@pytest.mark.unit
@pytest.mark.regression
def test_name_base_and_person_list_invariants() -> None:
    """Verify NameBase/NamePerson reject blank/duplicate list entries and blank comments."""
    with pytest.raises(ModelFormatError, match="aliases cannot contain empty"):
        NameBase(raw="John", canonical="John", aliases=["   "])

    with pytest.raises(ModelFormatError, match="Duplicate entries found in aliases"):
        NamePerson(raw="John", canonical="John", aliases=["Jack", "Jack"])

    with pytest.raises(ModelFormatError, match="alt_spellings cannot contain empty"):
        NameBase(raw="John", canonical="John", alt_spellings=["   "])

    with pytest.raises(ModelFormatError, match="Duplicate entries found in alt_spellings"):
        NamePerson(raw="John", canonical="John", alt_spellings=["Jhon", "Jhon"])

    with pytest.raises(ModelFormatError, match="'comment' cannot be blank"):
        NameBase(raw="John", canonical="John", comment="   ")

    with pytest.raises(ModelFormatError, match="married cannot contain empty"):
        NamePerson(raw="Mary Smith", canonical="Mary Smith", married=["   "])

    with pytest.raises(ModelFormatError, match="Duplicate entries found in married"):
        NamePerson(raw="Mary Smith", canonical="Mary Smith", married=["Jones", "Jones"])


# ==============================================================================
# GROUP 2: NAMEPERSON INITIALIZATION, MUTATORS & SERIALIZATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_name_person_full_specification(sample_name_person: NamePerson) -> None:
    """Verify NamePerson instantiates with all attributes and constructs full_name."""
    person = sample_name_person
    assert person.raw == "Col. John Quincy Adams Jr."
    assert person.canonical == "John Quincy Adams Jr."
    assert person.prefix == "Col."
    assert person.given == "John"
    assert person.middle == "Quincy"
    assert person.surname == "Adams"
    assert person.suffix == "Jr."
    assert person.married == ["Adams-Smith"]
    assert person.aliases == ["Old Man Eloquent"]
    assert person.alt_spellings == ["Addams"]
    assert person.full_name == "Col. John Quincy Adams Jr."
    assert str(person) == "Col. John Quincy Adams Jr."
    assert "NamePerson(" in repr(person)


@pytest.mark.unit
def test_name_person_factory_auto_computes_canonical() -> None:
    """Verify NamePerson.create computes canonical from parts and validates raw."""
    person = NamePerson.create(
        raw="rev j smith",
        prefix="Rev.",
        given="John",
        surname="Smith",
    )
    assert person.canonical == "Rev. John Smith"
    assert person.full_name == "Rev. John Smith"

    mononym = NamePerson.create(raw="Aristotle")
    assert mononym.canonical == "Aristotle"
    assert mononym.full_name == "Aristotle"

    with pytest.raises(ModelFormatError, match="NamePerson 'raw' cannot be empty"):
        NamePerson.create(raw="   ")


@pytest.mark.unit
@pytest.mark.regression
def test_name_person_create_fallback_and_deduplication() -> None:
    """Verify NamePerson.create falls back to raw on blank parts and deduplicates lists."""
    person = NamePerson.create(
        raw="Socrates",
        prefix="   ",
        given="   ",
        middle="   ",
        surname="   ",
        suffix="   ",
    )
    assert person.canonical == "Socrates"
    assert person.full_name == "Socrates"

    deduped = NamePerson.create(
        raw="Mary Smith",
        married=["Jones", "  Jones  ", "Smith-Jones", "", "   "],
        aliases=["Molly", "  Molly  ", "Polly", ""],
        alt_spellings=["Smyth", "  Smyth  ", "Smythe", ""],
    )
    assert deduped.married == ["Jones", "Smith-Jones"]
    assert deduped.aliases == ["Molly", "Polly"]
    assert deduped.alt_spellings == ["Smyth", "Smythe"]


@pytest.mark.unit
def test_name_person_copy_on_write_mutators(sample_name_person: NamePerson) -> None:
    """Verify NamePerson mutators return distinct immutable copies and support clearing parts."""
    original = sample_name_person

    # update_raw & idempotency
    updated_raw = original.update_raw("President J. Q. Adams")
    assert updated_raw is not original
    assert updated_raw.raw == "President J. Q. Adams"
    assert updated_raw.update_raw("President J. Q. Adams") is updated_raw

    # update_canonical & idempotency
    updated_can = original.update_canonical("John Adams Jr.")
    assert updated_can is not original
    assert updated_can.canonical == "John Adams Jr."
    assert updated_can.update_canonical("John Adams Jr.") is updated_can

    # update_parts (partial update + explicit clearing via None or blank string)
    updated_parts = original.update_parts(prefix="Hon.", suffix="Esq.")
    assert updated_parts is not original
    assert updated_parts.prefix == "Hon."
    assert updated_parts.suffix == "Esq."
    assert updated_parts.full_name == "Hon. John Quincy Adams Esq."

    cleared_parts = updated_parts.update_parts(prefix=None, middle="   ")
    assert cleared_parts.prefix is None
    assert cleared_parts.middle is None
    assert cleared_parts.given == "John"

    # add_married & remove_married
    with_married = original.add_married("Adams-Lee")
    assert with_married is not original
    assert "Adams-Lee" in with_married.married
    assert with_married.add_married("Adams-Lee") is with_married

    with_removed_married = with_married.remove_married("Adams-Smith")
    assert with_removed_married is not with_married
    assert "Adams-Smith" not in with_removed_married.married
    assert with_removed_married.remove_married("NONEXISTENT") is with_removed_married
    assert with_removed_married.remove_married("   ") is with_removed_married

    # add_alias & remove_alias
    with_alias = original.add_alias("Diplomat")
    assert with_alias is not original
    assert "Diplomat" in with_alias.aliases
    assert with_alias.add_alias("Diplomat") is with_alias

    with_removed_alias = with_alias.remove_alias("Old Man Eloquent")
    assert with_removed_alias is not with_alias
    assert "Old Man Eloquent" not in with_removed_alias.aliases
    assert with_removed_alias.remove_alias("NONEXISTENT") is with_removed_alias

    # add_spelling & remove_spelling
    with_spelling = original.add_spelling("Adames")
    assert with_spelling is not original
    assert "Adames" in with_spelling.alt_spellings
    assert with_spelling.add_spelling("Adames") is with_spelling

    with_removed_spelling = with_spelling.remove_spelling("Addams")
    assert with_removed_spelling is not with_spelling
    assert "Addams" not in with_removed_spelling.alt_spellings
    assert with_removed_spelling.remove_spelling("NONEXISTENT") is with_removed_spelling

    # update_comment & idempotency + clearing to None
    with_comment = original.update_comment("Revised biographical comment.")
    assert with_comment is not original
    assert with_comment.comment == "Revised biographical comment."
    assert with_comment.update_comment("Revised biographical comment.") is with_comment
    assert with_comment.update_comment(None).comment is None
    assert original.update_comment(None) is original


@pytest.mark.unit
@pytest.mark.regression
def test_name_person_mutator_empty_string_rejections(
    sample_name_person: NamePerson, failure_note_blank_text: str
) -> None:
    """Verify NamePerson mutators reject blank or whitespace inputs."""
    with pytest.raises(ModelFormatError, match="Raw name cannot be empty"):
        sample_name_person.update_raw(failure_note_blank_text)

    with pytest.raises(ModelFormatError, match="Canonical name cannot be empty"):
        sample_name_person.update_canonical(failure_note_blank_text)

    with pytest.raises(ModelFormatError, match="Alias cannot be empty"):
        sample_name_person.add_alias(failure_note_blank_text)

    with pytest.raises(ModelFormatError, match="Alternate spelling cannot be empty"):
        sample_name_person.add_spelling(failure_note_blank_text)

    with pytest.raises(ModelFormatError, match="Married name cannot be empty"):
        sample_name_person.add_married(failure_note_blank_text)


@pytest.mark.unit
def test_name_person_serialization_round_trips(sample_name_person: NamePerson) -> None:
    """Verify NamePerson dict/JSON serialization, optional field omission, and legacy keys."""
    payload = sample_name_person.to_dict()
    assert payload["raw"] == "Col. John Quincy Adams Jr."
    assert payload["prefix"] == "Col."
    assert payload["married"] == ["Adams-Smith"]
    assert NamePerson.from_dict(payload) == sample_name_person

    with_comment = NamePerson.create(
        raw="Benjamin Franklin",
        canonical="Benjamin Franklin",
        comment="Founding father and printer.",
    )
    assert with_comment.to_dict()["comment"] == "Founding father and printer."
    assert NamePerson.from_dict(with_comment.to_dict()).comment == "Founding father and printer."

    mononym = NamePerson.create(raw="Plato", canonical="Plato", surname="Plato")
    mono_data = mononym.to_dict()
    for omitted in ("prefix", "given", "middle", "suffix", "comment"):
        assert omitted not in mono_data

    given_only = NamePerson.create(raw="Aristotle", canonical="Aristotle", given="Aristotle")
    assert "surname" not in given_only.to_dict()

    legacy_payload: dict[str, Any] = {
        "raw_name": "Mary Smith",
        "canonical_name": "Mary Smith",
        "married_names": ["Jones"],
        "alternate_spellings": ["Smyth"],
        "notes": "Legacy note text.",
    }
    restored = NamePerson.from_dict(legacy_payload)
    assert restored.married == ["Jones"]
    assert restored.alt_spellings == ["Smyth"]
    assert restored.comment == "Legacy note text."

    json_str = sample_name_person.to_json()
    assert NamePerson.from_json(json_str) == sample_name_person


# ==============================================================================
# GROUP 3: MULTILINGUAL & NON-ENGLISH ONOMASTIC EDGE CASES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "prefix", "given", "surname", "expected_full"),
    [
        (
            "M. René François Lévesque",
            "M.",
            "René François",
            "Lévesque",
            "M. René François Lévesque",
        ),
        (
            "Iníon Siobhán Ní Dhomhnaill",
            "Iníon",
            "Siobhán",
            "Ní Dhomhnaill",
            "Iníon Siobhán Ní Dhomhnaill",
        ),
        ("Hr. Björn Åkesson", "Hr.", "Björn", "Åkesson", "Hr. Björn Åkesson"),
        ("Vincent van Gogh", None, "Vincent", "van Gogh", "Vincent van Gogh"),
        ("Пётр Ильич Чайковский", None, "Пётр Ильич", "Чайковский", "Пётр Ильич Чайковский"),
        ("徳川 家康", None, "家康", "徳川", "家康 徳川"),
    ],
)
def test_name_person_multilingual_unicode_support(
    raw: str, prefix: str | None, given: str, surname: str, expected_full: str
) -> None:
    """Verify NamePerson preserves diacritics, particles, and non-Latin scripts."""
    person = NamePerson.create(raw=raw, prefix=prefix, given=given, surname=surname)
    assert person.full_name == expected_full
    restored = NamePerson.from_dict(person.to_dict())
    assert restored == person


# ==============================================================================
# GROUP 4: HISTORICVARIANT & NAMETHING CREATION, MUTATORS & SERIALIZATION
# ==============================================================================


@pytest.mark.unit
def test_historic_variant_creation_validation_and_serialization(
    sample_historic_variant: HistoricVariant,
    golden_time_period: TimePeriod,
) -> None:
    """Verify HistoricVariant invariants, factory errors, and dict round-trips."""
    variant = sample_historic_variant
    assert str(variant) == "Manchester"
    assert "HistoricVariant(" in repr(variant)

    payload = variant.to_dict()
    assert payload["valid_period"]["start_date"] == {"date": "1751", "modifier": "EXACT"}
    assert HistoricVariant.from_dict(payload) == variant

    minimal = HistoricVariant.create(raw="Bow", historic_name_type="colloquial")
    assert minimal.historic_name_type == HistoricNameType.COLLOQUIAL
    assert "valid_period" not in minimal.to_dict()
    assert "comment" not in minimal.to_dict()

    with_period_obj = HistoricVariant.from_dict({"raw": "Bow", "valid_period": golden_time_period})
    assert with_period_obj.valid_period == golden_time_period

    with pytest.raises(ModelFormatError, match="'raw' cannot be empty"):
        HistoricVariant(raw="   ", name="Valid Name")
    with pytest.raises(ModelFormatError, match="'name' cannot be empty"):
        HistoricVariant(raw="Valid Raw", name="   ")
    with pytest.raises(ModelFormatError, match="'comment' cannot be blank"):
        HistoricVariant(raw="Valid Raw", name="Valid Name", comment="   ")
    with pytest.raises(ModelFormatError, match="'raw' cannot be empty"):
        HistoricVariant.create(raw="   ")
    with pytest.raises(ModelFormatError, match="Invalid HistoricNameType value"):
        HistoricVariant.create(raw="Bow", historic_name_type="BAD_TYPE")
    with pytest.raises(ModelFormatError, match="Invalid HistoricNameType type"):
        HistoricVariant.create(raw="Bow", historic_name_type=123)  # type: ignore[arg-type]


@pytest.mark.unit
def test_name_thing_creation_mutators_and_serialization(
    sample_name_thing: NameThing,
    sample_historic_variant: HistoricVariant,
    golden_time_period: TimePeriod,
) -> None:
    """Verify NameThing factory, variant mutators, and dict/JSON round-trips."""
    thing = sample_name_thing
    assert str(thing) == "Manchester"
    assert "NameThing(" in repr(thing)

    base = NameBase(raw="Base", canonical="Base")
    assert str(base) == "Base"
    assert repr(base) == (
        "NameBase(raw='Base', canonical='Base', aliases=[], alt_spellings=[], comment=None)"
    )

    assert NameThing.create(raw="Penacook", canonical="   ").canonical == "Penacook"
    with pytest.raises(ModelFormatError, match="NameThing 'raw' cannot be empty"):
        NameThing.create(raw="   ")

    deduped = NameThing.create(
        raw="Bow",
        aliases=["Bow Town", "  Bow Town  ", "Bow Center", ""],
        alt_spellings=["Bowe", "  Bowe  ", "Bow Mills", ""],
    )
    assert deduped.aliases == ["Bow Town", "Bow Center"]
    assert deduped.alt_spellings == ["Bowe", "Bow Mills"]

    # add_historic_variant (new + idempotent duplicate)
    with_added = thing.add_historic_variant(
        raw="Amoskeag",
        name="Amoskeag Village",
        historic_name_type=HistoricNameType.INDIGENOUS,
        valid_period=golden_time_period,
        comment="Native settlement at the falls.",
    )
    assert len(with_added.historic) == 2
    assert (
        with_added.add_historic_variant(
            raw="Amoskeag",
            name="Amoskeag Village",
            historic_name_type=HistoricNameType.INDIGENOUS,
            valid_period=golden_time_period,
            comment="Native settlement at the falls.",
        )
        is with_added
    )

    with_removed = with_added.remove_historic_variant("Derryfield")
    assert len(with_removed.historic) == 1
    assert with_removed.remove_historic_variant("NONEXISTENT") is with_removed
    assert with_removed.remove_historic_variant("   ") is with_removed

    # Serialization round-trip & legacy keys
    payload = thing.to_dict()
    assert NameThing.from_dict(payload) == thing

    with_comment = NameThing.create(raw="Concord", comment="State capital.")
    assert with_comment.to_dict()["comment"] == "State capital."
    assert NameThing.from_dict(with_comment.to_dict()).comment == "State capital."

    mixed_historic = NameThing.from_dict(
        {
            "raw_name": "City of Bow",
            "canonical_name": "Bow",
            "alternate_spellings": ["Bowe"],
            "notes": "Town note.",
            "historic": [
                {"raw": "Bow Mills", "historic_name_type": "COLLOQUIAL"},
                sample_historic_variant,
                "ignored_item",
            ],
        }
    )
    assert mixed_historic.canonical == "Bow"
    assert mixed_historic.comment == "Town note."
    assert len(mixed_historic.historic) == 2

    non_list_historic = NameThing.from_dict({"raw": "Bow", "historic": "not-a-list"})
    assert non_list_historic.historic == []

    json_str = thing.to_json()
    assert NameThing.from_json(json_str) == thing


# ==============================================================================
# GROUP 5: DEFENSIVE DESERIALIZER, IMMUTABILITY & ALIASES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_name_deserializer_defensive_errors(failure_note_blank_text: str) -> None:
    """Verify NamePerson, NameThing, and HistoricVariant deserializers reject malformed payloads."""
    with pytest.raises(ModelFormatError, match="payload must be a dictionary"):
        NamePerson.from_dict("not-a-dict")  # type: ignore[arg-type]
    with pytest.raises(ModelFormatError, match="Missing required field 'raw'"):
        NamePerson.from_dict({"raw": failure_note_blank_text})
    with pytest.raises(ModelFormatError, match="Failed to parse NamePerson JSON string"):
        NamePerson.from_json("{broken json")

    with pytest.raises(ModelFormatError, match="payload must be a dictionary"):
        NameThing.from_dict(["not", "dict"])  # type: ignore[arg-type]
    with pytest.raises(ModelFormatError, match="Missing required field 'raw'"):
        NameThing.from_dict({"raw": failure_note_blank_text})
    with pytest.raises(ModelFormatError, match="Failed to parse NameThing JSON string"):
        NameThing.from_json("{broken json")

    with pytest.raises(ModelFormatError, match="HistoricVariant payload must be a dictionary"):
        HistoricVariant.from_dict(["not", "dict"])  # type: ignore[arg-type]
    with pytest.raises(ModelFormatError, match="Missing required field 'raw'"):
        HistoricVariant.from_dict({"raw": failure_note_blank_text})


@pytest.mark.unit
def test_name_models_immutability_introspection_and_aliases(
    sample_name_person: NamePerson, sample_name_thing: NameThing
) -> None:
    """Verify frozen immutability, .help() introspection, and legacy aliases."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_name_person.given = "Jane"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_name_thing.canonical = "Concord"  # type: ignore[misc]

    assert NamePerson(raw="John", canonical="John").help(as_str=True) is not None
    assert NameThing(raw="Town", canonical="Town").help(as_str=True) is not None
    assert CanonicalName is NamePerson
    assert HistoricalName is NameThing
