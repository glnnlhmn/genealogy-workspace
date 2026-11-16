"""Path: tests/test_gda/test_entity/test_families/test_families_collection.py

Comprehensive unit and regression test suite for Families collection manager.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gda.core.enums.vital import PedigreeType, UnionType
from gda.entity.families.collection import Families
from gda.entity.families.errors import FamilyNotFoundError, FamilyValidationError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.tombstone import Tombstone
from gda.model.entity.family import Family

__version__ = "1.0.0+build.3"


@pytest.mark.unit
def test_families_init_empty_and_with_list(
    make_family: Callable[..., Family],
) -> None:
    """Verify Families initialization with empty state and pre-populated list."""
    empty = Families()
    assert len(empty) == 0
    assert empty.is_dirty is False

    f1 = make_family("FAM-000001").mark_dirty()
    f2 = make_family("FAM-000002", partner_ids=["IND-000010", "IND-000011"])
    populated = Families([f1, f2])
    assert len(populated) == 2
    assert populated.is_dirty is True
    assert populated.dirty_entities() == [f1]
    populated.mark_clean()
    assert populated.is_dirty is False
    assert populated.dirty_entities() == []


@pytest.mark.unit
def test_families_contains_getitem_get_and_graveyard_helpers(
    make_family: Callable[..., Family],
    active_family: Family,
    tombstoned_family: Family,
) -> None:
    """Verify __contains__, __getitem__, get(), get_any(), find_tombstoned(), and resolve_active()."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    sup_fam = make_family(
        "FAM-000003",
        tombstone=Tombstone[FamilyID]().retire(timestamp=now, superseded_by=active_family.id),
    )
    cyc1 = make_family(
        "FAM-000004",
        tombstone=Tombstone[FamilyID]().retire(timestamp=now, superseded_by=FamilyID("FAM-000005")),
    )
    cyc2 = make_family(
        "FAM-000005",
        tombstone=Tombstone[FamilyID]().retire(timestamp=now, superseded_by=FamilyID("FAM-000004")),
    )
    coll = Families([active_family, tombstoned_family, sup_fam, cyc1, cyc2])

    assert active_family.id in coll
    assert "FAM-000001" in coll
    assert active_family.canonical_urn in coll
    assert tombstoned_family.id not in coll
    assert "FAM-000002" not in coll
    assert tombstoned_family.canonical_urn not in coll
    assert "FAM-999999" not in coll
    assert "urn:gda:fam:missing" not in coll
    assert 12345 not in coll  # type: ignore[operator]

    assert coll[active_family.id] is active_family
    assert coll["FAM-000001"] is active_family
    assert coll[active_family.canonical_urn] is active_family
    assert coll.get("FAM-000001") is active_family
    assert coll.get("FAM-999999") is None

    assert coll.get_any("FAM-000002") is tombstoned_family
    assert coll.get_any("FAM-999999") is None
    assert coll.get_any(12345) is None  # type: ignore[arg-type]
    assert len(coll.find_tombstoned()) == 4
    assert coll.resolve_active("FAM-000001") is active_family
    assert coll.resolve_active("FAM-000003") is active_family
    assert coll.resolve_active("FAM-000002") is None
    assert coll.resolve_active("FAM-000004") is None
    assert coll.resolve_active("FAM-999999") is None

    with pytest.raises(FamilyNotFoundError, match="not found"):
        _ = coll["FAM-999999"]
    with pytest.raises(FamilyNotFoundError, match="not found"):
        _ = coll[12345]  # type: ignore[index]
    with pytest.raises(FamilyNotFoundError, match="tombstoned"):
        _ = coll[tombstoned_family.id]


@pytest.mark.unit
def test_families_iteration_excludes_tombstoned_and_iter_all_includes(
    active_family: Family,
    tombstoned_family: Family,
) -> None:
    """Verify __iter__ yields only active entities while iter_all yields all."""
    coll = Families([active_family, tombstoned_family])
    assert list(coll) == [active_family]
    assert list(coll.iter_all()) == [active_family, tombstoned_family]


@pytest.mark.regression
def test_families_add_and_update_type_guards_and_reindexing(
    make_family: Callable[..., Family],
) -> None:
    """Verify add and update enforce Family type and re-index all secondary buckets."""
    coll = Families()
    with pytest.raises(TypeError, match="Expected Family instance"):
        coll.add("not-a-fam")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Expected Family instance"):
        coll.update("not-a-fam")  # type: ignore[arg-type]

    missing = make_family("FAM-000099")
    with pytest.raises(FamilyNotFoundError, match="not found in registry"):
        coll.update(missing)

    fam1 = make_family(
        "FAM-000001",
        canonical_urn="urn:gda:fam:orig_1",
        partner_ids=["IND-000001", "IND-000002"],
        children=[ChildLink.create("IND-000003", PedigreeType.BIRTH)],
        union=FamilyUnion.create(union_type=UnionType.MARRIED),
    )
    coll.add(fam1)

    fam1_updated = make_family(
        "FAM-000001",
        canonical_urn="urn:gda:fam:updated_1",
        partner_ids=["IND-000004"],
        children=[ChildLink.create("IND-000005", PedigreeType.ADOPTED)],
        union=FamilyUnion.create(union_type=UnionType.CIVIL_UNION),
    )
    coll.update(fam1_updated)

    assert "urn:gda:fam:orig_1" not in coll._urn_index
    assert coll["urn:gda:fam:updated_1"] is fam1_updated
    assert coll.find_by_partner("IND-000001") == []
    assert coll.find_by_partner(IndividualID("IND-000004")) == [fam1_updated]
    assert coll.find_by_child("IND-000003") == []
    assert coll.find_by_child(IndividualID("IND-000005")) == [fam1_updated]
    assert coll.find_by_union_type("MARRIED") == []
    assert coll.find_by_union_type(UnionType.CIVIL_UNION) == [fam1_updated]


@pytest.mark.unit
def test_families_update_retains_non_empty_shared_buckets_and_unchanged_fields(
    make_family: Callable[..., Family],
) -> None:
    """Verify update retains index buckets when other families share them."""
    f1 = make_family(
        "FAM-000001",
        partner_ids=["IND-000001", "IND-000002"],
        children=[ChildLink.create("IND-000003", PedigreeType.BIRTH)],
        union=FamilyUnion.create(union_type=UnionType.MARRIED),
    )
    f2 = make_family(
        "FAM-000002",
        canonical_urn="urn:gda:fam:second_2",
        partner_ids=["IND-000001", "IND-000002"],
        children=[ChildLink.create("IND-000003", PedigreeType.BIRTH)],
        union=FamilyUnion.create(union_type=UnionType.MARRIED),
    )
    coll = Families([f1, f2])

    f2_updated = make_family(
        "FAM-000002",
        canonical_urn="urn:gda:fam:second_2",
        partner_ids=[],
        children=[],
        union=FamilyUnion.create(union_type=UnionType.COMMON_LAW),
    )
    coll.update(f2_updated)
    assert UnionType.MARRIED in coll._union_type_index
    assert IndividualID("IND-000001") in coll._partner_index
    assert IndividualID("IND-000003") in coll._child_index

    f2_final = make_family(
        "FAM-000002",
        canonical_urn="urn:gda:fam:second_2",
        partner_ids=[],
        children=[],
        union=FamilyUnion.create(union_type=UnionType.COMMON_LAW),
    )
    coll.update(f2_final)
    assert coll["FAM-000002"] is f2_final


@pytest.mark.unit
def test_families_create_variants_and_validation_guards(
    mock_individuals_collection: MagicMock,
) -> None:
    """Verify Families.create supports partnered, partnerless, explicit URN, and FK validation."""
    coll = Families()

    with pytest.raises(FamilyValidationError, match="Partner individual"):
        coll.create(
            partner_ids=["IND-999999"],
            individuals_collection=mock_individuals_collection,
        )

    with pytest.raises(FamilyValidationError, match="Child individual"):
        coll.create(
            partner_ids=["IND-000001"],
            children=[("IND-999999", PedigreeType.BIRTH)],
            individuals_collection=mock_individuals_collection,
        )

    # 1. Partnerless family auto-URN
    f1 = coll.create(
        partner_ids=[],
        children=[("IND-000003", PedigreeType.BIRTH)],
        individuals_collection=mock_individuals_collection,
    )
    assert f1.id == FamilyID("FAM-000001")
    assert f1.canonical_urn == "urn:gda:fam:union_f000001"

    # 2. Partnered family auto-URN
    f2 = coll.create(
        partner_ids=[IndividualID("IND-000001"), "IND-000002"],
        individuals_collection=mock_individuals_collection,
    )
    assert f2.canonical_urn == "urn:gda:fam:ind_000001_ind_000002_f000002"

    # 3. Explicit canonical_urn without individuals_collection
    f3 = coll.create(
        partner_ids=["IND-000010"],
        canonical_urn="urn:gda:fam:custom_unit",
    )
    assert f3.canonical_urn == "urn:gda:fam:custom_unit"


@pytest.mark.unit
def test_families_persistence_and_file_facades(
    active_family: Family,
    tmp_path: Path,
) -> None:
    """Verify from_database, load_from_db, save_to_db, refresh, import_file, and export_file facades."""
    with (
        patch("gda.entity.families.collection.load_from_db", return_value=1) as mock_load,
        patch("gda.entity.families.collection.save_to_db", return_value=1) as mock_save,
    ):
        db_coll = Families.from_database()
        mock_load.assert_called_once_with(db_coll)

        db_coll.add(active_family)
        assert db_coll.save_to_db() == 1
        assert db_coll.is_dirty is False
        mock_save.assert_called_once_with(db_coll)

        assert db_coll.load_from_db() == 1
        assert db_coll.refresh() == 1
        assert len(db_coll) == 0

    out_file = tmp_path / "families.json"
    coll = Families([active_family])
    assert coll.export_file(out_file) == 1
    fresh = Families()
    assert fresh.import_file(out_file) == 1
    assert len(fresh) == 1
