"""Path: tests/test_gda/test_entity/test_individuals/test_individuals_collection.py

Comprehensive unit and regression test suite for Individuals collection manager.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gda.core.errors import ModelFormatError
from gda.entity.individuals.collection import Individuals
from gda.entity.individuals.errors import (
    IndividualNotFoundError,
    IndividualValidationError,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, SiteID
from gda.model.base.name import NamePerson
from gda.model.base.tombstone import Tombstone
from gda.model.entity.individual import Individual

__version__ = "1.0.0+build.3"


@pytest.mark.unit
def test_individuals_init_empty_and_with_list(
    make_individual: Callable[..., Individual],
) -> None:
    """Verify Individuals initialization with empty state and pre-populated list."""
    empty = Individuals()
    assert len(empty) == 0
    assert empty.is_dirty is False

    i1 = make_individual("IND-000001").mark_dirty()
    i2 = make_individual("IND-000002", name="Abigail Smith")
    populated = Individuals([i1, i2])
    assert len(populated) == 2
    assert populated.is_dirty is True
    assert populated.dirty_entities() == [i1]
    populated.mark_clean()
    assert populated.is_dirty is False
    assert populated.dirty_entities() == []


@pytest.mark.unit
def test_individuals_contains_getitem_get_and_graveyard_helpers(
    make_individual: Callable[..., Individual],
    active_individual: Individual,
    tombstoned_individual: Individual,
) -> None:
    """Verify __contains__, __getitem__, get(), get_any(), find_tombstoned(), and resolve_active()."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    sup_ind = make_individual(
        "IND-000003",
        tombstone=Tombstone[IndividualID]().retire(
            timestamp=now, superseded_by=active_individual.id
        ),
    )
    cyc1 = make_individual(
        "IND-000004",
        tombstone=Tombstone[IndividualID]().retire(
            timestamp=now, superseded_by=IndividualID("IND-000005")
        ),
    )
    cyc2 = make_individual(
        "IND-000005",
        tombstone=Tombstone[IndividualID]().retire(
            timestamp=now, superseded_by=IndividualID("IND-000004")
        ),
    )
    coll = Individuals([active_individual, tombstoned_individual, sup_ind, cyc1, cyc2])

    assert active_individual.id in coll
    assert "IND-000001" in coll
    assert active_individual.canonical_urn in coll
    assert tombstoned_individual.id not in coll
    assert "IND-000002" not in coll
    assert tombstoned_individual.canonical_urn not in coll
    assert "IND-999999" not in coll
    assert "urn:gda:ind:missing" not in coll
    assert 12345 not in coll  # type: ignore[operator]

    assert coll[active_individual.id] is active_individual
    assert coll["IND-000001"] is active_individual
    assert coll[active_individual.canonical_urn] is active_individual
    assert coll.get("IND-000001") is active_individual
    assert coll.get("IND-999999") is None

    assert coll.get_any("IND-000002") is tombstoned_individual
    assert coll.get_any("IND-999999") is None
    assert coll.get_any(12345) is None  # type: ignore[arg-type]
    assert len(coll.find_tombstoned()) == 4
    assert coll.resolve_active("IND-000001") is active_individual
    assert coll.resolve_active("IND-000003") is active_individual
    assert coll.resolve_active("IND-000002") is None
    assert coll.resolve_active("IND-000004") is None
    assert coll.resolve_active("IND-999999") is None

    with pytest.raises(IndividualNotFoundError, match="not found"):
        _ = coll["IND-999999"]
    with pytest.raises(IndividualNotFoundError, match="not found"):
        _ = coll[12345]  # type: ignore[index]
    with pytest.raises(IndividualNotFoundError, match="tombstoned"):
        _ = coll[tombstoned_individual.id]


@pytest.mark.unit
def test_individuals_iteration_excludes_tombstoned_and_iter_all_includes(
    active_individual: Individual,
    tombstoned_individual: Individual,
) -> None:
    """Verify __iter__ yields only active entities while iter_all yields all."""
    coll = Individuals([active_individual, tombstoned_individual])
    assert list(coll) == [active_individual]
    assert list(coll.iter_all()) == [active_individual, tombstoned_individual]


@pytest.mark.regression
def test_individuals_add_and_update_type_guards_and_reindexing(
    make_individual: Callable[..., Individual],
) -> None:
    """Verify add and update enforce Individual type and re-index all secondary buckets."""
    coll = Individuals()
    with pytest.raises(TypeError, match="Expected Individual instance"):
        coll.add("not-an-ind")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Expected Individual instance"):
        coll.update("not-an-ind")  # type: ignore[arg-type]

    missing = make_individual("IND-000099")
    with pytest.raises(IndividualNotFoundError, match="not found in registry"):
        coll.update(missing)

    name1 = (
        NamePerson.create(raw="Abigail Smith", given="Abigail", surname="Smith")
        .add_alias("Abby")
        .add_married("Adams")
    )
    ind1 = make_individual(
        "IND-000001",
        name=name1,
        canonical_urn="urn:gda:ind:smith_abigail",
        birth_place_id="SID-000001",
        death_place_id="LOC-000001",
    )
    coll.add(ind1)
    assert coll.find_by_alias("Abby") == [ind1]
    assert coll.find_by_alias("   ") == []
    assert coll.find_by_surname("   ") == []

    name2 = NamePerson.create(raw="Abigail Quincy", given="Abigail", surname="Quincy").add_alias(
        "Nabby"
    )
    ind1_updated = make_individual(
        "IND-000001",
        name=name2,
        canonical_urn="urn:gda:ind:quincy_abigail",
        birth_place_id="LOC-000002",
        death_place_id="SID-000002",
    )
    coll.update(ind1_updated)

    assert "abby" not in coll._alias_index
    assert coll._alias_index["nabby"] == {ind1.id}
    assert "urn:gda:ind:smith_abigail" not in coll._urn_index
    assert coll["urn:gda:ind:quincy_abigail"] is ind1_updated
    assert coll.find_by_surname("Smith") == []
    assert coll.find_by_surname("Adams") == []
    assert coll.find_by_surname("Quincy") == [ind1_updated]
    assert coll.find_by_location("LOC-000001") == []
    assert coll.find_by_location(LocationID("LOC-000002")) == [ind1_updated]
    assert coll.find_by_site("SID-000001") == []
    assert coll.find_by_site(SiteID("SID-000002")) == [ind1_updated]


@pytest.mark.unit
def test_individuals_update_retains_non_empty_shared_buckets_and_mononym(
    make_individual: Callable[..., Individual],
) -> None:
    """Verify update retains index buckets when other individuals share them and handles mononyms."""
    name1 = NamePerson.create(raw="John Adams", given="John", surname="Adams").add_alias(
        "Shared Alias"
    )
    ind1 = make_individual(
        "IND-000001",
        name=name1,
        birth_place_id="LOC-000001",
        death_place_id="SID-000001",
    )
    name2 = NamePerson.create(raw="Samuel Adams", given="Samuel", surname="Adams").add_alias(
        "Shared Alias"
    )
    ind2 = make_individual(
        "IND-000002",
        name=name2,
        canonical_urn="urn:gda:ind:adams_samuel",
        birth_place_id="LOC-000001",
        death_place_id="SID-000001",
    )
    coll = Individuals([ind1, ind2])
    assert coll._alias_index["shared alias"] == {ind1.id, ind2.id}

    # Update ind2 to a mononym (surname=None) with no birth/death places and same URN
    mono_name = NamePerson(raw="Madonna", canonical="Madonna", given="Madonna", surname=None)
    ind2_updated = make_individual(
        "IND-000002",
        name=mono_name,
        canonical_urn="urn:gda:ind:adams_samuel",
        birth_place_id=None,
        death_place_id=None,
    )
    coll.update(ind2_updated)

    assert coll._alias_index["shared alias"] == {ind1.id}
    assert "adams" in coll._surname_index
    assert LocationID("LOC-000001") in coll._location_index
    assert SiteID("SID-000001") in coll._site_index

    # Clear _alias_index and update ind1 to exercise key not in _alias_index branch
    coll._alias_index.clear()
    ind1_again = make_individual(
        "IND-000001",
        name="John Adams",
        birth_place_id="LOC-000001",
        death_place_id="SID-000001",
    )
    coll.update(ind1_again)


@pytest.mark.unit
def test_individuals_create_variants_and_validation_guards(
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
) -> None:
    """Verify Individuals.create supports NamePerson/str, mononym, auto/explicit URN, and FK validation."""
    coll = Individuals()

    with pytest.raises(ModelFormatError, match="cannot be blank"):
        coll.create(name="   ")

    with pytest.raises(IndividualValidationError, match="Birth place location"):
        coll.create(
            name="John Adams",
            birth_place_id="LOC-999999",
            locations_collection=mock_locations_collection,
        )

    with pytest.raises(IndividualValidationError, match="Death place site"):
        coll.create(
            name="John Adams",
            death_place_id="SID-999999",
            sites_collection=mock_sites_collection,
        )

    # 1. Create with str name, alternate_names, married_names, and auto-URN
    i1 = coll.create(
        name="Abigail Smith",
        gender="F",
        birth_date="1744-11-22",
        alternate_names=["Abby", "   "],
        married_names=["Adams", "   "],
        birth_place_id="LOC-000001",
        death_place_id="SID-000001",
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )
    assert i1.id == IndividualID("IND-000001")
    assert i1.canonical_urn == "urn:gda:ind:abigail_smith_i000001"

    # 2. Create with NamePerson object and explicit canonical_urn
    np = NamePerson.create(raw="John Quincy Adams", given="John Quincy", surname="Adams")
    i2 = coll.create(
        name=np,
        canonical_urn="urn:gda:ind:custom:jqa",
        birth_date="1767-07-11",
    )
    assert i2.canonical_urn == "urn:gda:ind:custom:jqa"

    # 3. Create with single-word mononym string
    i3 = coll.create(name="Pocahontas", gender="F")
    assert i3.given == "Pocahontas"
    assert i3.surname is None


@pytest.mark.unit
def test_individuals_persistence_and_file_facades(
    active_individual: Individual,
    tmp_path: Path,
) -> None:
    """Verify from_database, load_from_db, save_to_db, refresh, import_file, and export_file facades."""
    with (
        patch("gda.entity.individuals.collection.load_from_db", return_value=1) as mock_load,
        patch("gda.entity.individuals.collection.save_to_db", return_value=1) as mock_save,
    ):
        db_coll = Individuals.from_database()
        mock_load.assert_called_once_with(db_coll)

        db_coll.add(active_individual)
        assert db_coll.save_to_db() == 1
        assert db_coll.is_dirty is False
        mock_save.assert_called_once_with(db_coll)

        assert db_coll.load_from_db() == 1
        assert db_coll.refresh() == 1
        assert len(db_coll) == 0

    out_file = tmp_path / "individuals.json"
    coll = Individuals([active_individual])
    assert coll.export_file(out_file) == 1
    fresh = Individuals()
    assert fresh.import_file(out_file) == 1
    assert len(fresh) == 1
