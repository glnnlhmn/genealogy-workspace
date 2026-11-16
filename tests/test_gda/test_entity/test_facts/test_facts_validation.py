"""Path: tests/test_gda/test_entity/test_facts/test_facts_validation.py

Comprehensive test suite for gda.entity.facts.validation.
"""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from gda.core.enums.core import AssociatedRole, FactType
from gda.entity.facts.collection import Facts
from gda.entity.facts.errors import FactValidationError
from gda.entity.facts.validation import (
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_fact,
    valid_urn,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, IndividualID, LocationID, SiteID
from gda.model.base.tombstone import Tombstone
from gda.model.entity.fact import Fact, FactParticipant

__version__ = "1.0.0+build.2"


@pytest.mark.unit
def test_valid_urn_and_valid_fact_checks(
    make_fact: Callable[..., Fact],
) -> None:
    """Verify valid_urn and valid_fact enforce URN, title, fact_type, and subject invariants."""
    assert valid_urn("urn:gda:fact:ind_000001:birth_f000001") is True

    with pytest.raises(FactValidationError, match="Invalid canonical_urn format"):
        valid_urn("")
    with pytest.raises(FactValidationError, match="Invalid canonical_urn format"):
        valid_urn("urn:gda:site:wrong_prefix")
    with pytest.raises(FactValidationError, match="Contains empty or adjacent delimiters"):
        valid_urn("urn:gda:fact:ind_000001::birth")

    fact = make_fact("FID-000001")
    assert valid_fact(fact) is True

    blank_title_fact = make_fact("FID-000002")
    object.__setattr__(blank_title_fact, "title", "   ")
    with pytest.raises(FactValidationError, match="title cannot be blank"):
        valid_fact(blank_title_fact)

    bad_type_fact = make_fact("FID-000003")
    object.__setattr__(bad_type_fact, "fact_type", "NOT_AN_ENUM")
    with pytest.raises(FactValidationError, match="must be a FactType enum"):
        valid_fact(bad_type_fact)

    bad_subj_fact = make_fact("FID-000004")
    object.__setattr__(bad_subj_fact, "primary_subject_id", "NOT_AN_ID")
    with pytest.raises(FactValidationError, match="must be IndividualID or FamilyID"):
        valid_fact(bad_subj_fact)


@pytest.mark.unit
def test_valid_collection_references_checks_optional_fks(
    make_fact: Callable[..., Fact],
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
    mock_individuals_collection: MagicMock,
    mock_families_collection: MagicMock,
) -> None:
    """Verify valid_collection_references passes when FKs are None or valid, and fails when invalid."""
    f_none = make_fact("FID-000001", location_id=None, site_id=None)
    f_valid = make_fact("FID-000002", location_id="LOC-000001", site_id="SID-000001")
    f_fam = make_fact(
        "FID-000005",
        fact_type=FactType.MARRIAGE,
        primary_subject_id="FAM-000001",
        location_id=None,
        site_id=None,
    )
    coll = Facts([f_none, f_valid, f_fam])
    assert (
        valid_collection_references(
            coll,
            locations_collection=mock_locations_collection,
            sites_collection=mock_sites_collection,
            individuals_collection=mock_individuals_collection,
            families_collection=mock_families_collection,
        )
        is True
    )
    assert valid_collection_references(coll) is True

    f_bad_missing = make_fact(
        "FID-000003",
        primary_subject_id="IND-000099",
        location_id="LOC-000099",
        site_id="SID-000099",
        participants=[FactParticipant.create("IND-000098", AssociatedRole.WITNESS)],
    )
    f_bad_fam = make_fact(
        "FID-000006",
        fact_type=FactType.MARRIAGE,
        primary_subject_id="FAM-000099",
    )
    f_bad_prefix = make_fact("FID-000004")
    object.__setattr__(f_bad_prefix, "primary_subject_id", "BAD-SUBJ")
    object.__setattr__(f_bad_prefix, "location_id", "BAD-1")
    object.__setattr__(f_bad_prefix, "site_id", "BAD-2")
    bad_coll = Facts([f_bad_missing, f_bad_fam, f_bad_prefix])
    assert (
        valid_collection_references(
            bad_coll,
            locations_collection=mock_locations_collection,
            sites_collection=mock_sites_collection,
            individuals_collection=mock_individuals_collection,
            families_collection=mock_families_collection,
        )
        is False
    )


@pytest.mark.unit
def test_valid_collection_tombstones_checks_all_supersession_branches(
    make_fact: Callable[..., Fact],
) -> None:
    """Verify valid_collection_tombstones validates self, missing, and deprecated replacements."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    active = make_fact("FID-000001")
    dead_no_sup = make_fact(
        "FID-000002",
        tombstone=Tombstone[FactID]().retire(timestamp=now),
    )
    dead_valid_sup = make_fact(
        "FID-000003",
        tombstone=Tombstone[FactID]().retire(timestamp=now, superseded_by=FactID("FID-000001")),
    )
    clean_coll = Facts([active, dead_no_sup, dead_valid_sup])
    assert valid_collection_tombstones(clean_coll) is True

    dead_self = make_fact(
        "FID-000004",
        tombstone=Tombstone[FactID]().retire(timestamp=now),
    )
    object.__setattr__(dead_self.tombstone, "superseded_by", FactID("FID-000004"))

    dead_missing = make_fact(
        "FID-000005",
        tombstone=Tombstone[FactID]().retire(timestamp=now, superseded_by=FactID("FID-000099")),
    )
    dead_to_dead = make_fact(
        "FID-000006",
        tombstone=Tombstone[FactID]().retire(timestamp=now, superseded_by=FactID("FID-000002")),
    )
    bad_coll = Facts([active, dead_no_sup, dead_self, dead_missing, dead_to_dead])
    assert valid_collection_tombstones(bad_coll) is False


@pytest.mark.unit
def test_valid_collection_indexes_and_valid_collection_all(
    make_fact: Callable[..., Fact],
) -> None:
    """Verify valid_collection_indexes detects desynchronization across all secondary indexes."""
    f1 = make_fact("FID-000001", location_id=None, site_id=None, participants=[])
    f2 = make_fact(
        "FID-000002",
        canonical_urn="urn:gda:fact:event_2",
        location_id="LOC-000001",
        site_id="SID-000001",
    )
    coll = Facts([f1, f2])
    assert valid_collection_indexes(coll) is True
    assert valid_collection_all(coll) is True

    # 1. URN mismatch, missing URN, dangling URN, and cleared buckets
    coll._urn_index["urn:gda:fact:event_2"] = f1.id
    coll._urn_index.pop(f1.canonical_urn, None)
    coll._urn_index["urn:gda:fact:dangling"] = FactID("FID-999999")
    coll._subject_index.clear()
    coll._type_index.clear()
    coll._location_index.clear()
    coll._site_index.clear()
    coll._participant_index.clear()
    assert valid_collection_indexes(coll) is False

    # 2. Bucket exists but entity ID missing from each bucket
    coll2 = Facts([f1, f2])
    coll2._subject_index[f2.primary_subject_id].discard(f2.id)
    coll2._type_index[f2.fact_type].discard(f2.id)
    coll2._location_index[LocationID("LOC-000001")].discard(f2.id)
    coll2._site_index[SiteID("SID-000001")].discard(f2.id)
    coll2._participant_index[IndividualID("IND-000010")].discard(f2.id)
    assert valid_collection_indexes(coll2) is False
    assert valid_collection_all(coll2) is False
