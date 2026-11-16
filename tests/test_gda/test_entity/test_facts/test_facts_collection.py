"""Path: tests/test_gda/test_entity/test_facts/test_facts_collection.py

Comprehensive unit and regression test suite for Facts collection manager.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gda.core.enums.core import AssociatedRole, FactType
from gda.core.errors import ModelFormatError
from gda.entity.facts.collection import Facts
from gda.entity.facts.errors import FactNotFoundError, FactValidationError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, FamilyID, IndividualID, LocationID, SiteID
from gda.model.base.tombstone import Tombstone
from gda.model.entity.fact import Fact, FactParticipant

__version__ = "1.0.0+build.2"


@pytest.mark.unit
def test_facts_init_empty_and_with_list(make_fact: Callable[..., Fact]) -> None:
    """Verify Facts initialization with empty state and pre-populated list."""
    empty = Facts()
    assert len(empty) == 0
    assert empty.is_dirty is False

    f1 = make_fact("FID-000001").mark_dirty()
    f2 = make_fact(
        "FID-000002",
        fact_type=FactType.MARRIAGE,
        title="Marriage of John and Abigail",
        primary_subject_id=FamilyID("FAM-000001"),
    )
    populated = Facts([f1, f2])
    assert len(populated) == 2
    assert populated.is_dirty is True
    assert populated.dirty_entities() == [f1]
    populated.mark_clean()
    assert populated.is_dirty is False
    assert populated.dirty_entities() == []


@pytest.mark.unit
def test_facts_contains_getitem_get_and_graveyard_helpers(
    make_fact: Callable[..., Fact],
    active_fact: Fact,
    tombstoned_fact: Fact,
) -> None:
    """Verify __contains__, __getitem__, get(), get_any(), find_tombstoned(), and resolve_active()."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    sup_fact = make_fact(
        "FID-000003",
        tombstone=Tombstone[FactID]().retire(timestamp=now, superseded_by=active_fact.id),
    )
    cyc1 = make_fact(
        "FID-000004",
        tombstone=Tombstone[FactID]().retire(timestamp=now, superseded_by=FactID("FID-000005")),
    )
    cyc2 = make_fact(
        "FID-000005",
        tombstone=Tombstone[FactID]().retire(timestamp=now, superseded_by=FactID("FID-000004")),
    )
    coll = Facts([active_fact, tombstoned_fact, sup_fact, cyc1, cyc2])

    assert active_fact.id in coll
    assert "FID-000001" in coll
    assert active_fact.canonical_urn in coll
    assert tombstoned_fact.id not in coll
    assert "FID-000002" not in coll
    assert tombstoned_fact.canonical_urn not in coll
    assert "FID-999999" not in coll
    assert "urn:gda:fact:missing" not in coll
    assert 12345 not in coll  # type: ignore[operator]

    assert coll[active_fact.id] is active_fact
    assert coll["FID-000001"] is active_fact
    assert coll[active_fact.canonical_urn] is active_fact
    assert coll.get("FID-000001") is active_fact
    assert coll.get("FID-999999") is None

    assert coll.get_any("FID-000002") is tombstoned_fact
    assert coll.get_any("FID-999999") is None
    assert coll.get_any(12345) is None  # type: ignore[arg-type]
    assert len(coll.find_tombstoned()) == 4
    assert coll.resolve_active("FID-000001") is active_fact
    assert coll.resolve_active("FID-000003") is active_fact
    assert coll.resolve_active("FID-000002") is None
    assert coll.resolve_active("FID-000004") is None
    assert coll.resolve_active("FID-999999") is None

    with pytest.raises(FactNotFoundError, match="not found"):
        _ = coll["FID-999999"]
    with pytest.raises(FactNotFoundError, match="not found"):
        _ = coll[12345]  # type: ignore[index]
    with pytest.raises(FactNotFoundError, match="tombstoned"):
        _ = coll[tombstoned_fact.id]


@pytest.mark.unit
def test_facts_iteration_excludes_tombstoned_and_iter_all_includes(
    active_fact: Fact,
    tombstoned_fact: Fact,
) -> None:
    """Verify __iter__ yields only active entities while iter_all yields all."""
    coll = Facts([active_fact, tombstoned_fact])
    assert list(coll) == [active_fact]
    assert list(coll.iter_all()) == [active_fact, tombstoned_fact]


@pytest.mark.regression
def test_facts_add_and_update_type_guards_and_reindexing(
    make_fact: Callable[..., Fact],
) -> None:
    """Verify add and update enforce Fact type and re-index all secondary buckets."""
    coll = Facts()
    with pytest.raises(TypeError, match="Expected Fact instance"):
        coll.add("not-a-fact")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Expected Fact instance"):
        coll.update("not-a-fact")  # type: ignore[arg-type]

    missing = make_fact("FID-000099")
    with pytest.raises(FactNotFoundError, match="not found in registry"):
        coll.update(missing)

    fact = make_fact(
        "FID-000001",
        fact_type=FactType.BIRTH,
        primary_subject_id="IND-000001",
        canonical_urn="urn:gda:fact:birth_1",
        location_id="LOC-000001",
        site_id="SID-000001",
        participants=[FactParticipant.create("IND-000010", AssociatedRole.WITNESS)],
    )
    coll.add(fact)

    updated = make_fact(
        "FID-000001",
        fact_type=FactType.MARRIAGE,
        primary_subject_id="FAM-000001",
        canonical_urn="urn:gda:fact:marriage_1",
        location_id="LOC-000002",
        site_id="SID-000002",
        participants=[FactParticipant.create("IND-000011", AssociatedRole.CLERGY)],
    )
    coll.update(updated)

    assert "urn:gda:fact:birth_1" not in coll._urn_index
    assert coll["urn:gda:fact:marriage_1"] is updated
    assert coll.find_by_subject("IND-000001") == []
    assert coll.find_by_subject("FAM-000001") == [updated]
    assert coll.find_by_subject(FamilyID("FAM-000001")) == [updated]
    assert coll.find_by_type("BIRTH") == []
    assert coll.find_by_type(FactType.MARRIAGE) == [updated]
    assert coll.find_by_location("LOC-000001") == []
    assert coll.find_by_location(LocationID("LOC-000002")) == [updated]
    assert coll.find_by_site("SID-000001") == []
    assert coll.find_by_site(SiteID("SID-000002")) == [updated]
    assert coll.find_by_participant("IND-000010") == []
    assert coll.find_by_participant(IndividualID("IND-000011")) == [updated]


@pytest.mark.unit
def test_facts_update_retains_non_empty_shared_buckets_and_handles_unchanged_fields(
    make_fact: Callable[..., Fact],
) -> None:
    """Verify update retains index buckets when other facts share the bucket and handles None FKs."""
    f1 = make_fact(
        "FID-000001",
        fact_type=FactType.CENSUS,
        primary_subject_id="IND-000001",
        location_id="LOC-000001",
        site_id="SID-000001",
        participants=[FactParticipant.create("IND-000010", AssociatedRole.WITNESS)],
    )
    f2 = make_fact(
        "FID-000002",
        fact_type=FactType.CENSUS,
        primary_subject_id="IND-000001",
        canonical_urn="urn:gda:fact:census_2",
        location_id="LOC-000001",
        site_id="SID-000001",
        participants=[
            FactParticipant.create("IND-000010", AssociatedRole.WITNESS),
            FactParticipant.create("IND-000012", AssociatedRole.INFORMANT),
        ],
    )
    coll = Facts([f1, f2])

    f2_updated = make_fact(
        "FID-000002",
        fact_type=FactType.RESIDENCE,
        primary_subject_id="IND-000002",
        canonical_urn="urn:gda:fact:census_2",
        location_id=None,
        site_id=None,
        participants=[FactParticipant.create("IND-000012", AssociatedRole.INFORMANT)],
    )
    coll.update(f2_updated)
    assert IndividualID("IND-000001") in coll._subject_index
    assert FactType.CENSUS in coll._type_index
    assert LocationID("LOC-000001") in coll._location_index
    assert SiteID("SID-000001") in coll._site_index
    assert IndividualID("IND-000010") in coll._participant_index

    f2_final = make_fact(
        "FID-000002",
        title="Updated Residence Title",
        fact_type=FactType.RESIDENCE,
        primary_subject_id="IND-000002",
        canonical_urn="urn:gda:fact:census_2",
        location_id=None,
        site_id=None,
        participants=[FactParticipant.create("IND-000012", AssociatedRole.INFORMANT)],
    )
    coll.update(f2_final)
    assert coll["FID-000002"].title == "Updated Residence Title"


@pytest.mark.unit
def test_facts_create_variants_and_validation_guards(
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
    mock_individuals_collection: MagicMock,
    mock_families_collection: MagicMock,
) -> None:
    """Verify Facts.create supports auto-URN, explicit URN, and subject/participant/location/site FK validation."""
    coll = Facts()

    with pytest.raises(ModelFormatError, match="cannot be blank"):
        coll.create(
            fact_type=FactType.BIRTH,
            title="   ",
            primary_subject_id="IND-000001",
        )

    with pytest.raises(FactValidationError, match="Primary subject individual"):
        coll.create(
            fact_type=FactType.BIRTH,
            title="Birth",
            primary_subject_id="IND-999999",
            individuals_collection=mock_individuals_collection,
        )

    with pytest.raises(FactValidationError, match="Primary subject family"):
        coll.create(
            fact_type=FactType.MARRIAGE,
            title="Marriage",
            primary_subject_id="FAM-999999",
            families_collection=mock_families_collection,
        )

    with pytest.raises(FactValidationError, match="Participant individual"):
        coll.create(
            fact_type=FactType.BIRTH,
            title="Birth",
            primary_subject_id="IND-000001",
            participants=[FactParticipant.create("IND-999999", AssociatedRole.WITNESS)],
            individuals_collection=mock_individuals_collection,
        )

    with pytest.raises(FactValidationError, match="Governing location"):
        coll.create(
            fact_type=FactType.BIRTH,
            title="Birth",
            primary_subject_id="IND-000001",
            location_id="LOC-999999",
            locations_collection=mock_locations_collection,
        )

    with pytest.raises(FactValidationError, match="Venue site"):
        coll.create(
            fact_type=FactType.BIRTH,
            title="Birth",
            primary_subject_id="IND-000001",
            site_id="SID-999999",
            sites_collection=mock_sites_collection,
        )

    # 1. Auto-URN without location_id or site_id
    f1 = coll.create(
        fact_type="DEATH",
        title="Death of John",
        primary_subject_id="IND-000001",
        date="1910-04-02",
        participants=[FactParticipant.create("IND-000010", AssociatedRole.WITNESS)],
        individuals_collection=mock_individuals_collection,
    )
    assert f1.id == FactID("FID-000001")
    assert f1.canonical_urn == "urn:gda:fact:ind_000001:death_f000001"

    # 2. Explicit canonical_urn with valid location_id, site_id, and family subject
    f2 = coll.create(
        fact_type=FactType.BIRTH,
        title="Birth of John",
        primary_subject_id=IndividualID("IND-000001"),
        canonical_urn="urn:gda:fact:custom:birth_1",
        date="1842-05-14",
        location_id=LocationID("LOC-000001"),
        site_id=SiteID("SID-000001"),
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
        individuals_collection=mock_individuals_collection,
    )
    assert f2.canonical_urn == "urn:gda:fact:custom:birth_1"

    f3 = coll.create(
        fact_type=FactType.MARRIAGE,
        title="Marriage of Family",
        primary_subject_id=FamilyID("FAM-000001"),
        families_collection=mock_families_collection,
    )
    assert f3.primary_subject_id == FamilyID("FAM-000001")

    # Chronological sorting in find_by_subject (1842 BIRTH comes before 1910 DEATH)
    timeline = coll.find_by_subject("IND-000001")
    assert [f.id for f in timeline] == [f2.id, f1.id]


@pytest.mark.unit
def test_facts_persistence_and_file_facades(
    active_fact: Fact,
    tmp_path: Path,
) -> None:
    """Verify from_database, load_from_db, save_to_db, refresh, import_file, and export_file facades."""
    with (
        patch("gda.entity.facts.collection.load_from_db", return_value=1) as mock_load,
        patch("gda.entity.facts.collection.save_to_db", return_value=1) as mock_save,
    ):
        db_coll = Facts.from_database()
        mock_load.assert_called_once_with(db_coll)

        db_coll.add(active_fact)
        assert db_coll.save_to_db() == 1
        assert db_coll.is_dirty is False
        mock_save.assert_called_once_with(db_coll)

        assert db_coll.load_from_db() == 1
        assert db_coll.refresh() == 1
        assert len(db_coll) == 0

    out_file = tmp_path / "facts.json"
    coll = Facts([active_fact])
    assert coll.export_file(out_file) == 1
    fresh = Facts()
    assert fresh.import_file(out_file) == 1
    assert len(fresh) == 1
