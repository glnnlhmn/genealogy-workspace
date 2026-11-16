"""Path: tests/test_gda/test_entity/test_families/test_families_validation.py

Comprehensive test suite for gda.entity.families.validation.
"""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from gda.entity.families.collection import Families
from gda.entity.families.errors import FamilyValidationError
from gda.entity.families.validation import (
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_family,
    valid_urn,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.base.tombstone import Tombstone
from gda.model.entity.family import Family

__version__ = "1.0.0+build.1"


@pytest.mark.unit
def test_valid_urn_and_valid_family_checks(
    make_family: Callable[..., Family],
) -> None:
    """Verify valid_urn and valid_family enforce URN, union, partner, and child invariants."""
    assert valid_urn("urn:gda:fam:adams_smith_1764") is True

    with pytest.raises(FamilyValidationError, match="Invalid canonical_urn format"):
        valid_urn("")
    with pytest.raises(FamilyValidationError, match="Invalid canonical_urn format"):
        valid_urn("urn:gda:site:wrong_prefix")
    with pytest.raises(FamilyValidationError, match="Contains empty or adjacent delimiters"):
        valid_urn("urn:gda:fam:adams::smith")

    fam = make_family("FAM-000001")
    assert valid_family(fam) is True

    bad_union_fam = make_family("FAM-000002")
    object.__setattr__(bad_union_fam, "union", "NOT_A_UNION")
    with pytest.raises(FamilyValidationError, match="must be a FamilyUnion instance"):
        valid_family(bad_union_fam)

    too_many_partners = make_family("FAM-000003")
    object.__setattr__(
        too_many_partners,
        "partner_ids",
        [IndividualID("IND-000001"), IndividualID("IND-000002"), IndividualID("IND-000003")],
    )
    with pytest.raises(FamilyValidationError, match="cannot exceed 2 partners"):
        valid_family(too_many_partners)

    bad_partner_type = make_family("FAM-000004")
    object.__setattr__(bad_partner_type, "partner_ids", ["NOT_AN_ID"])
    with pytest.raises(FamilyValidationError, match="must contain IndividualID instances"):
        valid_family(bad_partner_type)

    bad_child_type = make_family("FAM-000005")
    object.__setattr__(bad_child_type, "children", ["NOT_A_CHILD_LINK"])
    with pytest.raises(FamilyValidationError, match="must contain ChildLink instances"):
        valid_family(bad_child_type)


@pytest.mark.unit
def test_valid_collection_references_checks_partner_and_child_fks(
    make_family: Callable[..., Family],
    mock_individuals_collection: MagicMock,
) -> None:
    """Verify valid_collection_references passes when FKs are valid and fails when invalid."""
    f_empty = make_family("FAM-000001", partner_ids=[], children=[])
    f_valid = make_family("FAM-000002")
    coll = Families([f_empty, f_valid])
    assert (
        valid_collection_references(
            coll,
            individuals_collection=mock_individuals_collection,
        )
        is True
    )
    assert valid_collection_references(coll) is True

    f_missing = make_family(
        "FAM-000003",
        partner_ids=["IND-000099"],
        children=[("IND-000098", "BIRTH")],
    )
    f_bad_prefix = make_family("FAM-000004", partner_ids=[], children=[])
    object.__setattr__(f_bad_prefix, "partner_ids", ["BAD-1"])
    mock_bad_child = MagicMock()
    mock_bad_child.child_id = "BAD-2"
    object.__setattr__(f_bad_prefix, "children", [mock_bad_child])

    bad_coll = Families([f_missing, f_bad_prefix])
    assert (
        valid_collection_references(
            bad_coll,
            individuals_collection=mock_individuals_collection,
        )
        is False
    )


@pytest.mark.unit
def test_valid_collection_tombstones_checks_all_supersession_branches(
    make_family: Callable[..., Family],
) -> None:
    """Verify valid_collection_tombstones validates self, missing, and deprecated replacements."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    active = make_family("FAM-000001")
    dead_no_sup = make_family(
        "FAM-000002",
        tombstone=Tombstone[FamilyID]().retire(timestamp=now),
    )
    dead_valid_sup = make_family(
        "FAM-000003",
        tombstone=Tombstone[FamilyID]().retire(timestamp=now, superseded_by=FamilyID("FAM-000001")),
    )
    clean_coll = Families([active, dead_no_sup, dead_valid_sup])
    assert valid_collection_tombstones(clean_coll) is True

    dead_self = make_family(
        "FAM-000004",
        tombstone=Tombstone[FamilyID]().retire(timestamp=now),
    )
    object.__setattr__(dead_self.tombstone, "superseded_by", FamilyID("FAM-000004"))

    dead_missing = make_family(
        "FAM-000005",
        tombstone=Tombstone[FamilyID]().retire(timestamp=now, superseded_by=FamilyID("FAM-000099")),
    )
    dead_to_dead = make_family(
        "FAM-000006",
        tombstone=Tombstone[FamilyID]().retire(timestamp=now, superseded_by=FamilyID("FAM-000002")),
    )
    bad_coll = Families([active, dead_no_sup, dead_self, dead_missing, dead_to_dead])
    assert valid_collection_tombstones(bad_coll) is False


@pytest.mark.unit
def test_valid_collection_indexes_and_valid_collection_all(
    make_family: Callable[..., Family],
) -> None:
    """Verify valid_collection_indexes detects desynchronization across all secondary indexes."""
    f1 = make_family("FAM-000001", partner_ids=[], children=[])
    f2 = make_family("FAM-000002", canonical_urn="urn:gda:fam:unit_2")
    coll = Families([f1, f2])
    assert valid_collection_indexes(coll) is True
    assert valid_collection_all(coll) is True

    # 1. URN mismatch, missing URN, dangling URN, and cleared buckets
    coll._urn_index["urn:gda:fam:unit_2"] = f1.id
    coll._urn_index.pop(f1.canonical_urn, None)
    coll._urn_index["urn:gda:fam:dangling"] = FamilyID("FAM-999999")
    coll._union_type_index.clear()
    coll._partner_index.clear()
    coll._child_index.clear()
    assert valid_collection_indexes(coll) is False

    # 2. Bucket exists but entity ID missing from each bucket
    coll2 = Families([f1, f2])
    coll2._union_type_index[f2.union_type].discard(f2.id)
    coll2._partner_index[IndividualID("IND-000001")].discard(f2.id)
    coll2._child_index[IndividualID("IND-000003")].discard(f2.id)
    assert valid_collection_indexes(coll2) is False
    assert valid_collection_all(coll2) is False
