"""Path: tests/test_gda/test_entity/test_individuals/test_individuals_validation.py

Comprehensive test suite for gda.entity.individuals.validation.
"""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from gda.entity.individuals.collection import Individuals
from gda.entity.individuals.errors import IndividualValidationError
from gda.entity.individuals.validation import (
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_individual,
    valid_urn,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, SiteID
from gda.model.base.name import NamePerson
from gda.model.base.tombstone import Tombstone
from gda.model.entity.individual import Individual

__version__ = "1.0.0+build.2"


@pytest.mark.unit
def test_valid_urn_and_valid_individual_checks(
    make_individual: Callable[..., Individual],
) -> None:
    """Verify valid_urn and valid_individual enforce URN, name, and gender invariants."""
    assert valid_urn("urn:gda:ind:smith_john_1842") is True

    with pytest.raises(IndividualValidationError, match="Invalid canonical_urn format"):
        valid_urn("")
    with pytest.raises(IndividualValidationError, match="Invalid canonical_urn format"):
        valid_urn("urn:gda:site:wrong_prefix")
    with pytest.raises(IndividualValidationError, match="Contains empty or adjacent delimiters"):
        valid_urn("urn:gda:ind:smith::john")

    ind = make_individual("IND-000001")
    assert valid_individual(ind) is True

    blank_name_ind = make_individual("IND-000002")
    object.__setattr__(blank_name_ind.name, "canonical", "   ")
    with pytest.raises(IndividualValidationError, match="canonical name cannot be blank"):
        valid_individual(blank_name_ind)

    bad_gender_ind = make_individual("IND-000003")
    object.__setattr__(bad_gender_ind, "gender", "NOT_A_GENDER_ATOM")
    with pytest.raises(IndividualValidationError, match="must be a GenderAtom instance"):
        valid_individual(bad_gender_ind)


@pytest.mark.unit
def test_valid_collection_references_checks_optional_birth_and_death_place_fks(
    make_individual: Callable[..., Individual],
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
) -> None:
    """Verify valid_collection_references passes when FKs are None or valid, and fails when invalid."""
    i_none = make_individual("IND-000001", birth_place_id=None, death_place_id=None)
    i_valid = make_individual(
        "IND-000002",
        birth_place_id="LOC-000001",
        death_place_id="SID-000001",
    )
    coll = Individuals([i_none, i_valid])
    assert (
        valid_collection_references(
            coll,
            locations_collection=mock_locations_collection,
            sites_collection=mock_sites_collection,
        )
        is True
    )
    assert valid_collection_references(coll) is True

    i_bad_missing = make_individual(
        "IND-000003",
        birth_place_id="LOC-000099",
        death_place_id="SID-000099",
    )
    i_bad_type = make_individual("IND-000004")
    object.__setattr__(i_bad_type, "birth_place_id", "BAD-1")
    object.__setattr__(i_bad_type, "death_place_id", "BAD-2")
    bad_coll = Individuals([i_bad_missing, i_bad_type])
    assert (
        valid_collection_references(
            bad_coll,
            locations_collection=mock_locations_collection,
            sites_collection=mock_sites_collection,
        )
        is False
    )


@pytest.mark.unit
def test_valid_collection_tombstones_checks_all_supersession_branches(
    make_individual: Callable[..., Individual],
) -> None:
    """Verify valid_collection_tombstones validates self, missing, and deprecated replacements."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    active = make_individual("IND-000001")
    dead_no_sup = make_individual(
        "IND-000002",
        tombstone=Tombstone[IndividualID]().retire(timestamp=now),
    )
    dead_valid_sup = make_individual(
        "IND-000003",
        tombstone=Tombstone[IndividualID]().retire(
            timestamp=now, superseded_by=IndividualID("IND-000001")
        ),
    )
    clean_coll = Individuals([active, dead_no_sup, dead_valid_sup])
    assert valid_collection_tombstones(clean_coll) is True

    dead_self = make_individual(
        "IND-000004",
        tombstone=Tombstone[IndividualID]().retire(timestamp=now),
    )
    object.__setattr__(dead_self.tombstone, "superseded_by", IndividualID("IND-000004"))

    dead_missing = make_individual(
        "IND-000005",
        tombstone=Tombstone[IndividualID]().retire(
            timestamp=now, superseded_by=IndividualID("IND-000099")
        ),
    )
    dead_to_dead = make_individual(
        "IND-000006",
        tombstone=Tombstone[IndividualID]().retire(
            timestamp=now, superseded_by=IndividualID("IND-000002")
        ),
    )
    bad_coll = Individuals([active, dead_no_sup, dead_self, dead_missing, dead_to_dead])
    assert valid_collection_tombstones(bad_coll) is False


@pytest.mark.unit
def test_valid_collection_indexes_and_valid_collection_all(
    make_individual: Callable[..., Individual],
) -> None:
    """Verify valid_collection_indexes detects desynchronization across all secondary indexes."""
    i1 = make_individual("IND-000001", birth_place_id=None, death_place_id=None)
    name2 = NamePerson.create(raw="Abigail Smith", given="Abigail", surname="Smith").add_alias(
        "Abby"
    )
    i2 = make_individual(
        "IND-000002",
        name=name2,
        canonical_urn="urn:gda:ind:smith_abigail",
        birth_place_id="LOC-000001",
        death_place_id="SID-000001",
    )
    coll = Individuals([i1, i2])
    assert valid_collection_indexes(coll) is True
    assert valid_collection_all(coll) is True

    # 1. URN mismatch, missing URN, dangling URN, and cleared buckets
    coll._urn_index["urn:gda:ind:smith_abigail"] = i1.id
    coll._urn_index.pop(i1.canonical_urn, None)
    coll._urn_index["urn:gda:ind:dangling"] = IndividualID("IND-999999")
    coll._alias_index.clear()
    coll._surname_index.clear()
    coll._location_index.clear()
    coll._site_index.clear()
    assert valid_collection_indexes(coll) is False

    # 2. Bucket exists but entity ID missing from each bucket
    coll2 = Individuals([i1, i2])
    coll2._alias_index["abby"].discard(i2.id)
    coll2._surname_index["smith"].discard(i2.id)
    coll2._location_index[LocationID("LOC-000001")].discard(i2.id)
    coll2._site_index[SiteID("SID-000001")].discard(i2.id)
    assert valid_collection_indexes(coll2) is False
    assert valid_collection_all(coll2) is False
