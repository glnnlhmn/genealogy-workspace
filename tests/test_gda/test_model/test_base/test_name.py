"""Path: tests/test_gda/test_model/test_base/test_name.py

Comprehensive test suite verifying NameBase, NamePerson, NameThing, and HistoricVariant.

Operational Role:
    Verifies that NameBase establishes foundational noun invariants, NamePerson formats
    discrete personal onomastic parts with prefix, suffix, and married names, and NameThing
    manages multi-phase HistoricVariant collections with temporal bounding. Equips all
    models with copy-on-write mutators, tests multilingual Unicode and non-English edge cases,
    and validates dictionary and JSON serialization round-trips with full branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from gda.core.errors import ModelFormatError
from gda.enums.vital import HistoricNameType
from gda.model.atom.date import DateModifier, DateString, EventDate
from gda.model.base.name import (
    CanonicalName,
    HistoricalName,
    HistoricVariant,
    NamePerson,
    NameThing,
)
from gda.model.base.time_period import TimePeriod

__version__ = "1.1.0+build.6"


# ==============================================================================
# GROUP 1: NAMEBASE INVARIANTS & BOUNDARIES
# Note: Verification of root noun invariants, whitespace rejections, and deduplication
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("blank_text", ["", " ", "\t\n"])
def test_name_base_blank_raw_raises_error(blank_text: str) -> None:
    """Verify NameBase raises ModelFormatError if raw string is empty or whitespace."""
    with pytest.raises(ModelFormatError, match="'raw' cannot be empty"):
        NamePerson(raw=blank_text, canonical="Valid Canonical")


@pytest.mark.regression
@pytest.mark.parametrize("blank_text", ["", " ", "\t\n"])
def test_name_base_blank_canonical_raises_error(blank_text: str) -> None:
    """Verify NameBase raises ModelFormatError if canonical string is empty or whitespace."""
    with pytest.raises(ModelFormatError, match="'canonical' cannot be empty"):
        NamePerson(raw="Valid Raw", canonical=blank_text)


@pytest.mark.regression
def test_name_base_duplicate_aliases_or_spellings_raises_error() -> None:
    """Verify NameBase constructor rejects duplicate aliases and alternate spellings."""
    with pytest.raises(ModelFormatError, match="Duplicate entries found in aliases"):
        NamePerson(
            raw="John",
            canonical="John",
            aliases=["Jack", "Jack"],
        )

    with pytest.raises(ModelFormatError, match="Duplicate entries found in alt_spellings"):
        NamePerson(
            raw="John",
            canonical="John",
            alt_spellings=["Jhon", "Jhon"],
        )


@pytest.mark.regression
def test_name_person_duplicate_married_names_raises_error() -> None:
    """Verify NamePerson constructor rejects duplicate married surnames."""
    with pytest.raises(ModelFormatError, match="Duplicate entries found in married"):
        NamePerson(
            raw="Mary Smith",
            canonical="Mary Smith",
            married=["Jones", "Jones"],
        )


# ==============================================================================
# GROUP 2: NAMEPERSON INITIALIZATION, MUTATORS & SERIALIZATION
# Note: Verification of onomastic formatting, married list mutators, and serialization
# ==============================================================================


@pytest.mark.unit
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


@pytest.mark.unit
def test_name_person_factory_auto_computes_canonical() -> None:
    """Verify NamePerson.create computes canonical from parts when omitted."""
    person = NamePerson.create(
        raw="rev j smith",
        prefix="Rev.",
        given="John",
        surname="Smith",
    )
    assert person.canonical == "Rev. John Smith"
    assert person.full_name == "Rev. John Smith"

    # Fallback to raw when parts are absent
    mononym = NamePerson.create(raw="Aristotle")
    assert mononym.canonical == "Aristotle"
    assert mononym.full_name == "Aristotle"


@pytest.mark.regression
def test_name_person_create_filters_whitespace_and_duplicates() -> None:
    """Verify NamePerson.create cleanly filters empty strings and duplicate lists."""
    person = NamePerson.create(
        raw="Mary Smith",
        married=["Jones", "  Jones  ", "Smith-Jones", "", "   "],
        aliases=["Molly", "  Molly  ", "Polly", ""],
        alt_spellings=["Smyth", "  Smyth  ", "Smythe", ""],
    )
    assert person.married == ["Jones", "Smith-Jones"]
    assert person.aliases == ["Molly", "Polly"]
    assert person.alt_spellings == ["Smyth", "Smythe"]


@pytest.mark.regression
def test_name_person_copy_on_write_mutators(sample_name_person: NamePerson) -> None:
    """Verify NamePerson mutators return distinct immutable copies."""
    original = sample_name_person

    # update_raw
    updated_raw = original.update_raw("President J. Q. Adams")
    assert updated_raw is not original
    assert updated_raw.raw == "President J. Q. Adams"
    assert updated_raw.canonical == original.canonical

    # update_canonical
    updated_can = original.update_canonical("John Adams Jr.")
    assert updated_can is not original
    assert updated_can.canonical == "John Adams Jr."

    # update_parts
    updated_parts = original.update_parts(prefix="Hon.", suffix="Esq.")
    assert updated_parts is not original
    assert updated_parts.prefix == "Hon."
    assert updated_parts.suffix == "Esq."
    assert updated_parts.full_name == "Hon. John Quincy Adams Esq."

    # add_married & remove_married
    with_married = original.add_married("Adams-Lee")
    assert with_married is not original
    assert "Adams-Lee" in with_married.married
    # idempotent addition
    assert with_married.add_married("Adams-Lee") is with_married

    with_removed_married = with_married.remove_married("Adams-Smith")
    assert with_removed_married is not with_married
    assert "Adams-Smith" not in with_removed_married.married
    # no-op removal
    assert with_removed_married.remove_married("NONEXISTENT") is with_removed_married

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

    # update_comment
    with_comment = original.update_comment("Revised biographical comment.")
    assert with_comment is not original
    assert with_comment.comment == "Revised biographical comment."


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


@pytest.mark.integration
def test_name_person_to_dict_and_from_dict_round_trip(
    sample_name_person: NamePerson,
) -> None:
    """Verify NamePerson dictionary serialization and deserialization."""
    payload = sample_name_person.to_dict()
    assert payload["raw"] == "Col. John Quincy Adams Jr."
    assert payload["canonical"] == "John Quincy Adams Jr."
    assert payload["prefix"] == "Col."
    assert payload["married"] == ["Adams-Smith"]

    restored = NamePerson.from_dict(payload)
    assert restored == sample_name_person


@pytest.mark.integration
def test_name_person_to_dict_omits_none_attributes() -> None:
    """Verify NamePerson.to_dict omits optional onomastic parts when None."""
    mononym = NamePerson.create(raw="Plato", canonical="Plato", surname="Plato")
    data = mononym.to_dict()
    assert "prefix" not in data
    assert "given" not in data
    assert "middle" not in data
    assert "suffix" not in data
    assert "comment" not in data
    assert data["surname"] == "Plato"

    given_only = NamePerson.create(raw="Aristotle", canonical="Aristotle", given="Aristotle")
    data_given = given_only.to_dict()
    assert "surname" not in data_given
    assert data_given["given"] == "Aristotle"


@pytest.mark.integration
def test_name_person_from_dict_legacy_key_support() -> None:
    """Verify NamePerson.from_dict correctly ingests legacy field names and fallbacks."""
    legacy_payload: dict[str, Any] = {
        "raw_name": "Mary Smith",
        "canonical_name": "Mary Smith",
        "married_names": ["Jones"],
        "alternate_spellings": ["Smyth"],
        "notes": "Legacy note text.",
    }
    restored = NamePerson.from_dict(legacy_payload)
    assert restored.raw == "Mary Smith"
    assert restored.canonical == "Mary Smith"
    assert restored.married == ["Jones"]
    assert restored.alt_spellings == ["Smyth"]
    assert restored.comment == "Legacy note text."

    raw_only_payload: dict[str, Any] = {"raw": "Widow Brown"}
    restored_raw_only = NamePerson.from_dict(raw_only_payload)
    assert restored_raw_only.raw == "Widow Brown"
    assert restored_raw_only.canonical == "Widow Brown"


@pytest.mark.integration
def test_name_person_json_serialization_round_trip(
    sample_name_person: NamePerson,
) -> None:
    """Verify NamePerson JSON string serialization round-trip."""
    json_str = sample_name_person.to_json()
    assert isinstance(json_str, str)
    assert "Adams-Smith" in json_str

    restored = NamePerson.from_json(json_str)
    assert restored == sample_name_person


# ==============================================================================
# GROUP 3: MULTILINGUAL & NON-ENGLISH ONOMASTIC EDGE CASES
# Note: Verification of diacritics, compound particles, and non-Latin scripts
# ==============================================================================


@pytest.mark.regression
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
        (
            "Don Gabriel García Márquez",
            "Don",
            "Gabriel",
            "García Márquez",
            "Don Gabriel García Márquez",
        ),
        (
            "Пётр Ильич Чайковский",
            None,
            "Пётр Ильич",
            "Чайковский",
            "Пётр Ильич Чайковский",
        ),
        ("徳川 家康", None, "家康", "徳川", "家康 徳川"),
    ],
)
def test_name_person_multilingual_unicode_support(
    raw: str, prefix: str | None, given: str, surname: str, expected_full: str
) -> None:
    """Verify NamePerson preserves diacritics, particles, and non-Latin scripts."""
    person = NamePerson.create(raw=raw, prefix=prefix, given=given, surname=surname)
    assert person.full_name == expected_full
    assert person.raw == raw

    data = person.to_dict()
    restored = NamePerson.from_dict(data)
    assert restored == person
    assert restored.to_json() is not None


# ==============================================================================
# GROUP 4: HISTORICVARIANT CREATION & SERIALIZATION
# Note: Verification of HistoricVariant temporal bounds and payload handling
# ==============================================================================


@pytest.mark.unit
def test_historic_variant_creation_and_properties(
    sample_historic_variant: HistoricVariant, golden_time_period: TimePeriod
) -> None:
    """Verify HistoricVariant instantiates with period and classification."""
    variant = sample_historic_variant
    assert variant.raw == "Derryfield"
    assert variant.name == "Manchester"
    assert variant.historic_name_type == HistoricNameType.HISTORICAL
    assert variant.valid_period == golden_time_period
    assert variant.comment == "Chartered in 1751, renamed Manchester in 1810."


@pytest.mark.regression
@pytest.mark.parametrize("blank_text", ["", " ", "\t\n"])
def test_historic_variant_blank_fields_raises_error(blank_text: str) -> None:
    """Verify HistoricVariant rejects empty raw or name fields."""
    with pytest.raises(ModelFormatError, match="'raw' cannot be empty"):
        HistoricVariant(raw=blank_text, name="Valid Name")

    with pytest.raises(ModelFormatError, match="'name' cannot be empty"):
        HistoricVariant(raw="Valid Raw", name=blank_text)


@pytest.mark.integration
def test_historic_variant_to_dict_and_from_dict_round_trip(
    sample_historic_variant: HistoricVariant,
) -> None:
    """Verify HistoricVariant dictionary serialization round-trip."""
    payload = sample_historic_variant.to_dict()
    assert payload["raw"] == "Derryfield"
    assert payload["name"] == "Manchester"
    assert payload["historic_name_type"] == "HISTORICAL"
    assert payload["valid_period"]["start_date"] == "1751"
    assert payload["valid_period"]["end_date"] == "1810"

    restored = HistoricVariant.from_dict(payload)
    assert restored == sample_historic_variant


@pytest.mark.integration
def test_historic_variant_to_dict_without_period_or_comment() -> None:
    """Verify HistoricVariant.to_dict handles valid_period is None."""
    variant = HistoricVariant.create(
        raw="Bow",
        name="Bow",
        valid_period=None,
        comment=None,
    )
    data = variant.to_dict()
    assert "valid_period" not in data
    assert "comment" not in data
    assert data["raw"] == "Bow"
    assert data["name"] == "Bow"


@pytest.mark.integration
def test_historic_variant_to_dict_partial_bounds_and_no_comment() -> None:
    """Verify HistoricVariant.to_dict serializes partial period bounds and handles None comment."""
    end_only_period = TimePeriod(
        end_date=EventDate(date=DateString("1850"), modifier=DateModifier.EXACT)
    )
    variant = HistoricVariant.create(
        raw="Bow Mills",
        name="Bow Mills",
        valid_period=end_only_period,
        comment=None,
    )
    data = variant.to_dict()
    assert data["valid_period"]["start_date"] is None
    assert data["valid_period"]["end_date"] == "1850"
    assert "comment" not in data


@pytest.mark.integration
def test_historic_variant_from_dict_with_direct_time_period_object(
    golden_time_period: TimePeriod,
) -> None:
    """Verify HistoricVariant.from_dict handles pre-constructed TimePeriod instance."""
    data = {
        "raw": "Bow",
        "valid_period": golden_time_period,
    }
    restored = HistoricVariant.from_dict(data)
    assert restored.valid_period == golden_time_period


@pytest.mark.integration
def test_historic_variant_from_dict_partial_period_branches() -> None:
    """Verify HistoricVariant parses open-ended start or end periods."""
    data_start = {
        "raw": "Bow Mills",
        "valid_period": {"start_date": "1727", "end_date": None},
    }
    restored_start = HistoricVariant.from_dict(data_start)
    assert restored_start.valid_period is not None
    assert str(restored_start.valid_period.start_date) == "1727"
    assert restored_start.valid_period.end_date is None

    data_end = {
        "raw": "Bow Mills",
        "valid_period": {"start_date": None, "end_date": "1850"},
    }
    restored_end = HistoricVariant.from_dict(data_end)
    assert restored_end.valid_period is not None
    assert str(restored_end.valid_period.end_date) == "1850"

    data_empty = {
        "raw": "Bow Mills",
        "valid_period": {"start_date": None, "end_date": None},
    }
    restored_empty = HistoricVariant.from_dict(data_empty)
    assert restored_empty.valid_period is None


# ==============================================================================
# GROUP 5: NAMETHING CREATION, MUTATORS & SERIALIZATION
# Note: Verification of multi-phase historic variants, aliases, and round-trips
# ==============================================================================


@pytest.mark.unit
def test_name_thing_creation_and_properties(sample_name_thing: NameThing) -> None:
    """Verify NameThing instantiates with canonical name and embedded variants."""
    thing = sample_name_thing
    assert thing.raw == "City of Manchester"
    assert thing.canonical == "Manchester"
    assert thing.aliases == ["Queen City"]
    assert thing.alt_spellings == ["Manchestir"]
    assert len(thing.historic) == 1
    assert thing.historic[0].name == "Manchester"
    assert str(thing) == "Manchester"


@pytest.mark.regression
def test_name_thing_create_filters_whitespace_and_duplicates() -> None:
    """Verify NameThing.create cleanly filters empty strings and duplicate lists."""
    thing = NameThing.create(
        raw="Bow",
        aliases=["Bow Town", "  Bow Town  ", "Bow Center", "", "  "],
        alt_spellings=["Bowe", "  Bowe  ", "Bow Mills", ""],
    )
    assert thing.aliases == ["Bow Town", "Bow Center"]
    assert thing.alt_spellings == ["Bowe", "Bow Mills"]


@pytest.mark.regression
def test_name_thing_add_and_remove_historic_variant(
    sample_name_thing: NameThing, golden_time_period: TimePeriod
) -> None:
    """Verify NameThing mutators append and remove HistoricVariant records."""
    original = sample_name_thing
    assert len(original.historic) == 1

    # add_historic_variant
    with_added = original.add_historic_variant(
        raw="Amoskeag",
        name="Amoskeag Village",
        historic_name_type=HistoricNameType.INDIGENOUS,
        valid_period=golden_time_period,
        comment="Native settlement at the falls.",
    )
    assert with_added is not original
    assert len(with_added.historic) == 2
    assert with_added.historic[1].raw == "Amoskeag"
    assert with_added.historic[1].historic_name_type == HistoricNameType.INDIGENOUS

    # remove_historic_variant
    with_removed = with_added.remove_historic_variant("Derryfield")
    assert with_removed is not with_added
    assert len(with_removed.historic) == 1
    assert with_removed.historic[0].raw == "Amoskeag"

    # no-op removal
    assert with_removed.remove_historic_variant("NONEXISTENT") is with_removed


@pytest.mark.integration
def test_name_thing_to_dict_and_from_dict_round_trip(
    sample_name_thing: NameThing,
) -> None:
    """Verify NameThing dictionary serialization and deserialization."""
    payload = sample_name_thing.to_dict()
    assert payload["raw"] == "City of Manchester"
    assert payload["canonical"] == "Manchester"
    assert payload["aliases"] == ["Queen City"]
    assert len(payload["historic"]) == 1

    restored = NameThing.from_dict(payload)
    assert restored == sample_name_thing


@pytest.mark.integration
def test_name_thing_to_dict_without_comment() -> None:
    """Verify NameThing.to_dict omits comment when None."""
    thing = NameThing.create(raw="Concord", canonical="Concord", comment=None)
    data = thing.to_dict()
    assert "comment" not in data
    assert data["raw"] == "Concord"


@pytest.mark.integration
def test_name_thing_from_dict_non_list_historic_payload() -> None:
    """Verify NameThing.from_dict safely handles non-list historic payloads."""
    data = {
        "raw": "Bow",
        "canonical": "Bow",
        "historic": "not-a-list",
    }
    restored = NameThing.from_dict(data)
    assert restored.raw == "Bow"
    assert restored.historic == []


@pytest.mark.integration
def test_name_thing_from_dict_with_direct_historic_variant_instances(
    sample_historic_variant: HistoricVariant,
) -> None:
    """Verify NameThing.from_dict handles mixed lists with direct HistoricVariant instances."""
    dict_variant = {
        "raw": "Bow Mills",
        "name": "Bow Mills",
        "historic_name_type": "COLLOQUIAL",
    }
    data = {
        "raw": "Manchester",
        "canonical": "Manchester",
        # Pass a dict, a HistoricVariant instance, and an unhandled item type to exercise all branches
        "historic": [dict_variant, sample_historic_variant, "invalid_item_to_ignore"],
    }
    restored = NameThing.from_dict(data)
    assert len(restored.historic) == 2
    assert restored.historic[0].raw == "Bow Mills"
    assert restored.historic[1] == sample_historic_variant


@pytest.mark.integration
def test_name_thing_from_dict_legacy_key_support() -> None:
    """Verify NameThing.from_dict handles legacy raw_name and canonical_name keys and fallbacks."""
    data = {
        "raw_name": "City of Bow",
        "canonical_name": "Bow",
        "alternate_spellings": ["Bowe"],
        "notes": "Town note.",
    }
    restored = NameThing.from_dict(data)
    assert restored.raw == "City of Bow"
    assert restored.canonical == "Bow"
    assert restored.alt_spellings == ["Bowe"]
    assert restored.comment == "Town note."

    raw_only = {"raw": "Concord"}
    restored_raw = NameThing.from_dict(raw_only)
    assert restored_raw.raw == "Concord"
    assert restored_raw.canonical == "Concord"


@pytest.mark.integration
def test_name_thing_json_serialization_round_trip(
    sample_name_thing: NameThing,
) -> None:
    """Verify NameThing JSON string serialization round-trip."""
    json_str = sample_name_thing.to_json()
    assert isinstance(json_str, str)
    assert "Queen City" in json_str

    restored = NameThing.from_json(json_str)
    assert restored == sample_name_thing


# ==============================================================================
# GROUP 6: DEFENSIVE DESERIALIZER & IMMUTABILITY CONTRACTS
# Note: Verification of malformed payload rejections and frozen enforcement
# ==============================================================================


@pytest.mark.regression
def test_name_deserializer_defensive_errors(failure_note_blank_text: str) -> None:
    """Verify NamePerson and NameThing deserializers reject malformed payloads."""
    with pytest.raises(ModelFormatError, match="payload must be a dictionary"):
        NamePerson.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'raw'"):
        NamePerson.from_dict({"given": "John"})

    with pytest.raises(ModelFormatError, match="Missing required field 'raw'"):
        NamePerson.from_dict({"raw": failure_note_blank_text})

    with pytest.raises(ModelFormatError, match="Failed to parse NamePerson JSON string"):
        NamePerson.from_json("{broken json")

    with pytest.raises(ModelFormatError, match="payload must be a dictionary"):
        NameThing.from_dict(["not", "dict"])  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'raw'"):
        NameThing.from_dict({"canonical": "Manchester"})

    with pytest.raises(ModelFormatError, match="Missing required field 'raw'"):
        NameThing.from_dict({"raw": failure_note_blank_text})

    with pytest.raises(ModelFormatError, match="Failed to parse NameThing JSON string"):
        NameThing.from_json("{broken json")

    with pytest.raises(ModelFormatError, match="HistoricVariant payload must be a dictionary"):
        HistoricVariant.from_dict(["not", "dict"])  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'raw'"):
        HistoricVariant.from_dict({"name": "Manchester"})

    with pytest.raises(ModelFormatError, match="Missing required field 'raw'"):
        HistoricVariant.from_dict({"raw": failure_note_blank_text})


@pytest.mark.regression
def test_name_models_immutability(
    sample_name_person: NamePerson, sample_name_thing: NameThing
) -> None:
    """Verify NamePerson, NameThing, and HistoricVariant are frozen dataclasses."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_name_person.given = "Jane"  # type: ignore[misc]

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_name_thing.canonical = "Concord"  # type: ignore[misc]

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_name_thing.historic[0].name = "New Manchester"  # type: ignore[misc]


@pytest.mark.regression
def test_name_models_introspection() -> None:
    """Verify .help() renders public member directories on naming models."""
    p = NamePerson(raw="John", canonical="John")
    help_p = p.help(as_str=True)
    assert help_p is not None
    assert "=== NamePerson Public Directory ===" in help_p
    assert "add_married" in help_p
    assert "update_parts" in help_p

    t = NameThing(raw="Town", canonical="Town")
    help_t = t.help(as_str=True)
    assert help_t is not None
    assert "=== NameThing Public Directory ===" in help_t
    assert "add_historic_variant" in help_t


@pytest.mark.unit
def test_backward_compatibility_aliases() -> None:
    """Verify legacy CanonicalName and HistoricalName aliases map directly."""
    assert CanonicalName is NamePerson
    assert HistoricalName is NameThing
