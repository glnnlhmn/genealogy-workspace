"""Path: tests/test_gda/test_engine/test_resolver.py

Atomized unit, regression, and smoke test suite for IndividualFamilyResolver.

Operational Role:
    Verifies kinship graph indexation, bidirectional queries, dynamic mutations,
    IntrospectableMixin documentation, edge deduplication, and safe entity eviction.
"""

from __future__ import annotations

import pytest

from gda.engine.resolver import IndividualFamilyResolver
from gda.enums.core import AssociatedRole
from gda.enums.vital import PedigreeType
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.base.audit import AuditStamp
from gda.model.base.family import ChildLink
from gda.model.base.name import CanonicalName
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.xref.individual_family_xref import IndividualFamilyXRef

__version__ = "1.0.0+build.3"


def _make_audit() -> AuditStamp:
    """Helper creating a valid AuditStamp."""
    now = IsoTimestamp.now_utc()
    return AuditStamp(created_at=now, updated_at=now)


# ==============================================================================
# GROUP 1: Initialization & Hydration Factories
# ==============================================================================


@pytest.mark.unit
def test_resolver_init_empty_state_and_introspection() -> None:
    """Verify clean initialization, zero edge count, and .help() discovery."""
    resolver = IndividualFamilyResolver()
    assert resolver.edge_count == 0
    assert resolver.last_compiled.value is not None
    assert resolver.export_xrefs() == []

    help_doc = IndividualFamilyResolver.help(as_str=True)
    assert help_doc is not None
    assert "IndividualFamilyResolver" in help_doc


@pytest.mark.smoke
def test_from_collections_smoke() -> None:
    """Verify bulk ingestion from collections of Individual and Family entities."""
    audit = _make_audit()
    ind = Individual(
        id=IndividualID("IND-000001"),
        name=CanonicalName(raw_name="John Doe", given="John", surname="Doe"),
        canonical_urn="urn:gda:ind:john_doe",
        audit=audit,
    )
    fam = Family(
        id=FamilyID("FAM-000001"),
        canonical_urn="urn:gda:fam:doe_family",
        partner_ids=[ind.id],
        audit=audit,
    )

    resolver = IndividualFamilyResolver.from_collections(
        individuals=[ind], families=[fam]
    )
    assert resolver.edge_count == 2
    assert resolver.get_families_as_partner(ind.id) == (fam.id,)


@pytest.mark.unit
def test_from_xrefs_bulk_hydration() -> None:
    """Verify hydrating directly from an iterable of IndividualFamilyXRef edges."""
    edge = IndividualFamilyXRef(
        xref_id="IND-000002::CHILD::FAM-000001",
        subject_id=IndividualID("IND-000002"),
        target_id=FamilyID("FAM-000001"),
        relation_type="CHILD",
    )
    resolver = IndividualFamilyResolver.from_xrefs([edge])
    assert resolver.edge_count == 1
    assert resolver.get_families_as_child(IndividualID("IND-000002")) == (
        FamilyID("FAM-000001"),
    )


# ==============================================================================
# GROUP 2: Edge Intake, Idempotency & Deduplication Branches
# ==============================================================================


@pytest.mark.regression
def test_add_xref_idempotent_and_non_family_targets() -> None:
    """Verify duplicate edge deduplication and non-family target relation handling."""
    resolver = IndividualFamilyResolver()
    p1 = IndividualID("IND-000001")
    p2 = IndividualID("IND-000002")

    edge_identity = IndividualFamilyXRef(
        xref_id="IND-000001::IDENTITY::IND-000001",
        subject_id=p1,
        target_id=p1,
        relation_type="IDENTITY",
    )
    resolver.add_xref(edge_identity)
    resolver.add_xref(edge_identity)  # Idempotent return branch
    assert resolver.edge_count == 1

    # PARTNER with non-family target
    edge_partner_non_fam = IndividualFamilyXRef(
        xref_id="IND-000001::PARTNER::IND-000002",
        subject_id=p1,
        target_id=p2,
        relation_type="PARTNER",
    )
    resolver.add_xref(edge_partner_non_fam)

    # CHILD with non-family target
    edge_child_non_fam = IndividualFamilyXRef(
        xref_id="IND-000001::CHILD::IND-000002",
        subject_id=p1,
        target_id=p2,
        relation_type="CHILD",
    )
    resolver.add_xref(edge_child_non_fam)
    assert resolver.edge_count == 3


@pytest.mark.regression
def test_add_xref_partner_and_child_already_in_family_lists() -> None:
    """Verify lines 95->105 and 102->105 when partner or child is already present in family lists."""
    resolver = IndividualFamilyResolver()
    p1 = IndividualID("IND-000001")
    c1 = IndividualID("IND-000002")
    fam = FamilyID("FAM-000001")

    # 1. Partner edge 1
    edge_partner_1 = IndividualFamilyXRef(
        xref_id="IND-000001::PARTNER::FAM-000001",
        subject_id=p1,
        target_id=fam,
        relation_type="PARTNER",
    )
    # Partner edge 2 (distinct key, but p1 already exists in _fam_to_partners)
    edge_partner_2 = IndividualFamilyXRef(
        xref_id="IND-000001::PARTNER::FAM-000001::SPOUSE",
        subject_id=p1,
        target_id=fam,
        relation_type="PARTNER",
        role=AssociatedRole.SPOUSE,
    )
    resolver.add_xref(edge_partner_1)
    resolver.add_xref(edge_partner_2)  # Exercises line 95->105

    # 2. Child edge 1
    edge_child_1 = IndividualFamilyXRef(
        xref_id="IND-000002::CHILD::FAM-000001",
        subject_id=c1,
        target_id=fam,
        relation_type="CHILD",
        role=PedigreeType.BIRTH,
    )
    # Child edge 2 (distinct key, but (c1, BIRTH) already exists in _fam_to_children)
    edge_child_2 = IndividualFamilyXRef(
        xref_id="IND-000002::CHILD::FAM-000001::ALT",
        subject_id=c1,
        target_id=fam,
        relation_type="CHILD",
        role=PedigreeType.BIRTH,
    )
    resolver.add_xref(edge_child_1)
    resolver.add_xref(edge_child_2)  # Exercises line 102->105

    assert resolver.edge_count == 4


# ==============================================================================
# GROUP 3: Kinship Graph Traversals
# ==============================================================================


@pytest.mark.unit
def test_spouses_children_and_parents_traversals() -> None:
    """Verify bidirectional kinship traversals across partners, children, and parents."""
    father = IndividualID("IND-000001")
    mother = IndividualID("IND-000002")
    child1 = IndividualID("IND-000003")
    child2 = IndividualID("IND-000004")
    stepchild = IndividualID("IND-000005")

    fam = Family(
        id=FamilyID("FAM-000001"),
        canonical_urn="urn:gda:fam:main_union",
        partner_ids=[father, mother],
        children=[
            ChildLink(child_id=child1, pedigree=PedigreeType.BIRTH),
            ChildLink(child_id=child2, pedigree=PedigreeType.ADOPTED),
            ChildLink(child_id=stepchild, pedigree=PedigreeType.STEP),
        ],
        audit=_make_audit(),
    )

    resolver = IndividualFamilyResolver()
    resolver.index_family(fam)

    # Spouses
    assert resolver.get_spouses(father) == (mother,)
    assert resolver.get_spouses(mother) == (father,)

    # Children
    assert resolver.get_children(father) == (child1, child2, stepchild)

    # Parents
    assert resolver.get_parents(child1) == (father, mother)

    # Pedigree lookups (first, middle, last, and missing child)
    assert resolver.get_pedigree_for_child(child1, fam.id) == PedigreeType.BIRTH
    assert resolver.get_pedigree_for_child(child2, fam.id) == PedigreeType.ADOPTED
    assert resolver.get_pedigree_for_child(stepchild, fam.id) == PedigreeType.STEP
    assert resolver.get_pedigree_for_child(IndividualID("IND-000099"), fam.id) is None


@pytest.mark.unit
def test_traversal_fallbacks_on_empty_and_unlinked_entities() -> None:
    """Verify lookups return empty tuples on missing entities and parentless families."""
    resolver = IndividualFamilyResolver()
    unlinked = IndividualID("IND-000099")

    assert resolver.get_families_as_partner(unlinked) == ()
    assert resolver.get_families_as_child(unlinked) == ()
    assert resolver.get_spouses(unlinked) == ()
    assert resolver.get_children(unlinked) == ()
    assert resolver.get_parents(unlinked) == ()

    # Family with children but no recorded parents
    fam_no_parents = Family(
        id=FamilyID("FAM-000002"),
        canonical_urn="urn:gda:fam:orphans",
        partner_ids=[],
        children=[ChildLink(child_id=unlinked, pedigree=PedigreeType.BIRTH)],
        audit=_make_audit(),
    )
    resolver.index_family(fam_no_parents)
    assert resolver.get_parents(unlinked) == ()


# ==============================================================================
# GROUP 4: In-Place Entity Eviction
# ==============================================================================


@pytest.mark.regression
def test_evict_individual_purges_all_referencing_edges() -> None:
    """Verify evicting an individual safely purges partner and child relationships."""
    ind1 = IndividualID("IND-000001")
    ind2 = IndividualID("IND-000002")
    child = IndividualID("IND-000003")

    fam = Family(
        id=FamilyID("FAM-000001"),
        canonical_urn="urn:gda:fam:multi_partner",
        partner_ids=[ind1, ind2],
        children=[ChildLink(child_id=child, pedigree=PedigreeType.BIRTH)],
        audit=_make_audit(),
    )

    resolver = IndividualFamilyResolver()
    resolver.index_family(fam)
    assert resolver.edge_count == 3

    # Evicting ind1 retains ind2 in the family
    resolver.evict_entity(ind1)
    assert resolver.get_spouses(ind2) == ()
    assert resolver.get_families_as_partner(ind1) == ()
    assert resolver.get_families_as_partner(ind2) == (fam.id,)

    # Evict child
    resolver.evict_entity(child)
    assert resolver.get_children(ind2) == ()
    assert resolver.get_families_as_child(child) == ()


@pytest.mark.regression
def test_evict_family_with_partners_and_children_cleanses_both() -> None:
    """Verify evicting a FamilyID clears both partner and child set references."""
    p1 = IndividualID("IND-000001")
    c1 = IndividualID("IND-000002")
    fam = Family(
        id=FamilyID("FAM-000001"),
        canonical_urn="urn:gda:fam:test_full_fam",
        partner_ids=[p1],
        children=[ChildLink(child_id=c1, pedigree=PedigreeType.BIRTH)],
        audit=_make_audit(),
    )

    resolver = IndividualFamilyResolver()
    resolver.index_family(fam)
    assert resolver.edge_count == 2

    resolver.evict_entity(fam.id)
    assert resolver.edge_count == 0
    assert resolver.get_families_as_partner(p1) == ()
    assert resolver.get_families_as_child(c1) == ()

    # Nonexistent entity eviction (noop early return branch)
    resolver.evict_entity(IndividualID("IND-000999"))
    assert resolver.edge_count == 0
