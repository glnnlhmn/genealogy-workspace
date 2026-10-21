"""Path: tests/test_gda/test_engine/test_fact_resolver.py

Atomized unit, regression, and smoke test suite for FactParticipantResolver.

Operational Role:
    Verifies inverted event indexation, role-filtered queries, bulk hydration,
    IntrospectableMixin documentation, edge deduplication, and safe eviction.
"""

from __future__ import annotations

import pytest

from gda.engine.fact_resolver import FactParticipantResolver
from gda.enums.core import AssociatedRole, FactType
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, IndividualID
from gda.model.base.audit import AuditStamp
from gda.model.entity.fact import Fact, FactParticipant
from gda.model.xref.fact_participant_xref import FactParticipantXRef

__version__ = "1.0.0+build.1"


def _make_audit() -> AuditStamp:
    """Helper creating a valid AuditStamp."""
    now = IsoTimestamp.now_utc()
    return AuditStamp(created_at=now, updated_at=now)


# ==============================================================================
# GROUP 1: Initialization & Hydration Factories
# ==============================================================================


@pytest.mark.unit
def test_resolver_init_empty() -> None:
    """Verify clean initialization, zero edge count, and valid last_compiled."""
    resolver = FactParticipantResolver()
    assert resolver.edge_count == 0
    assert resolver.last_compiled.value is not None
    assert resolver.export_xrefs() == []


@pytest.mark.unit
def test_resolver_introspectable_help() -> None:
    """Verify .help() returns Markdown documentation via IntrospectableMixin."""
    help_doc = FactParticipantResolver.help(as_str=True)
    assert help_doc is not None
    assert "FactParticipantResolver" in help_doc


@pytest.mark.smoke
def test_resolver_from_facts_smoke() -> None:
    """Verify bulk ingestion from an iterable of Fact domain entities."""
    audit = _make_audit()
    ind_witness = IndividualID("IND-000002")
    subject = IndividualID("IND-000001")
    fact = Fact(
        id=FactID("FID-000001"),
        canonical_urn="urn:gda:fact:marriage_event",
        fact_type=FactType.MARRIAGE,
        title="Marriage Ceremony",
        primary_subject_id=subject,
        participants=[
            FactParticipant(individual_id=ind_witness, role=AssociatedRole.WITNESS)
        ],
        audit=audit,
    )

    resolver = FactParticipantResolver.from_facts([fact])
    assert resolver.edge_count == 1
    assert resolver.get_facts_as_participant(ind_witness) == (fact.id,)
    assert resolver.get_participants_for_fact(fact.id) == (
        (ind_witness, AssociatedRole.WITNESS),
    )


@pytest.mark.unit
def test_resolver_from_xrefs() -> None:
    """Verify bulk instantiation from an iterable of FactParticipantXRef edges."""
    witness = IndividualID("IND-000002")
    subject = IndividualID("IND-000001")
    fact = FactID("FID-000001")
    edge = FactParticipantXRef(
        xref_id="E1",
        associated_ind_id=witness,
        fact_id=fact,
        primary_subject_id=subject,
        role=AssociatedRole.INFORMANT,
    )

    resolver = FactParticipantResolver.from_xrefs([edge])
    assert resolver.edge_count == 1
    assert resolver.get_facts_as_participant(witness) == (fact,)
    assert resolver.export_xrefs() == [edge]


# ==============================================================================
# GROUP 2: Edge Intake & Bidirectional Query Traversals
# ==============================================================================


@pytest.mark.unit
def test_get_facts_as_participant_all_and_filtered_by_role() -> None:
    """Verify querying facts with and without specific AssociatedRole filters."""
    witness = IndividualID("IND-000002")
    subject = IndividualID("IND-000001")
    f1 = FactID("FID-000001")
    f2 = FactID("FID-000002")

    resolver = FactParticipantResolver()
    resolver.add_xref(
        FactParticipantXRef(
            xref_id="E1",
            associated_ind_id=witness,
            fact_id=f1,
            primary_subject_id=subject,
            role=AssociatedRole.WITNESS,
        )
    )
    resolver.add_xref(
        FactParticipantXRef(
            xref_id="E2",
            associated_ind_id=witness,
            fact_id=f2,
            primary_subject_id=subject,
            role=AssociatedRole.INFORMANT,
        )
    )

    assert resolver.get_facts_as_participant(witness) == (f1, f2)
    assert resolver.get_facts_as_participant(witness, role=AssociatedRole.WITNESS) == (
        f1,
    )
    assert resolver.get_facts_as_participant(
        witness, role=AssociatedRole.INFORMANT
    ) == (f2,)
    assert resolver.get_facts_as_participant(witness, role=AssociatedRole.CLERGY) == ()


@pytest.mark.unit
def test_get_roles_for_individual() -> None:
    """Verify returning all unique roles an individual served in."""
    witness = IndividualID("IND-000002")
    subject = IndividualID("IND-000001")
    resolver = FactParticipantResolver()
    resolver.add_xref(
        FactParticipantXRef(
            xref_id="E1",
            associated_ind_id=witness,
            fact_id=FactID("FID-000001"),
            primary_subject_id=subject,
            role=AssociatedRole.WITNESS,
        )
    )
    resolver.add_xref(
        FactParticipantXRef(
            xref_id="E2",
            associated_ind_id=witness,
            fact_id=FactID("FID-000002"),
            primary_subject_id=subject,
            role=AssociatedRole.INFORMANT,
        )
    )

    roles = resolver.get_roles_for_individual(witness)
    assert AssociatedRole.WITNESS in roles
    assert AssociatedRole.INFORMANT in roles


@pytest.mark.unit
def test_traversal_fallbacks_unlinked() -> None:
    """Verify unindexed entities return empty tuples."""
    resolver = FactParticipantResolver()
    unlinked = IndividualID("IND-000999")
    unlinked_fact = FactID("FID-000999")

    assert resolver.get_facts_as_participant(unlinked) == ()
    assert resolver.get_participants_for_fact(unlinked_fact) == ()
    assert resolver.get_roles_for_individual(unlinked) == ()


@pytest.mark.regression
def test_add_duplicate_xref_idempotent() -> None:
    """Verify re-adding an edge with the same xref_id or participant entry is idempotent."""
    witness = IndividualID("IND-000002")
    subject = IndividualID("IND-000001")
    fact = FactID("FID-000001")
    edge1 = FactParticipantXRef(
        xref_id="E1",
        associated_ind_id=witness,
        fact_id=fact,
        primary_subject_id=subject,
        role=AssociatedRole.WITNESS,
    )
    edge2 = FactParticipantXRef(
        xref_id="E2",
        associated_ind_id=witness,
        fact_id=fact,
        primary_subject_id=subject,
        role=AssociatedRole.WITNESS,
    )

    resolver = FactParticipantResolver()
    resolver.add_xref(edge1)
    resolver.add_xref(edge1)  # Exact edge idempotency
    assert resolver.edge_count == 1

    resolver.add_xref(edge2)  # Duplicate entry deduplication in _fact_to_participants
    assert resolver.edge_count == 2
    assert len(resolver.get_participants_for_fact(fact)) == 1


# ==============================================================================
# GROUP 3: Individual & Fact Eviction Invariants
# ==============================================================================


@pytest.mark.regression
def test_evict_individual_purges_all_references() -> None:
    """Verify evicting an individual safely purges participation maps and fact links."""
    witness1 = IndividualID("IND-000002")
    witness2 = IndividualID("IND-000003")
    subject = IndividualID("IND-000001")
    fact = FactID("FID-000001")

    resolver = FactParticipantResolver()
    resolver.add_xref(
        FactParticipantXRef(
            xref_id="E1",
            associated_ind_id=witness1,
            fact_id=fact,
            primary_subject_id=subject,
            role=AssociatedRole.WITNESS,
        )
    )
    resolver.add_xref(
        FactParticipantXRef(
            xref_id="E2",
            associated_ind_id=witness2,
            fact_id=fact,
            primary_subject_id=subject,
            role=AssociatedRole.INFORMANT,
        )
    )
    assert resolver.edge_count == 2

    resolver.evict_individual(witness1)
    assert resolver.edge_count == 1
    assert resolver.get_facts_as_participant(witness1) == ()
    assert resolver.get_participants_for_fact(fact) == (
        (witness2, AssociatedRole.INFORMANT),
    )


@pytest.mark.regression
def test_evict_fact_purges_all_references() -> None:
    """Verify evicting a fact purges participant mappings for associated individuals."""
    witness = IndividualID("IND-000002")
    subject = IndividualID("IND-000001")
    fact = FactID("FID-000001")

    resolver = FactParticipantResolver()
    resolver.add_xref(
        FactParticipantXRef(
            xref_id="E1",
            associated_ind_id=witness,
            fact_id=fact,
            primary_subject_id=subject,
            role=AssociatedRole.WITNESS,
        )
    )
    assert resolver.edge_count == 1

    resolver.evict_fact(fact)
    assert resolver.edge_count == 0
    assert resolver.get_facts_as_participant(witness) == ()
    assert resolver.get_participants_for_fact(fact) == ()


@pytest.mark.regression
def test_evict_nonexistent_individual_or_fact_noop() -> None:
    """Verify evicting unknown individual or fact IDs is a safe no-op."""
    resolver = FactParticipantResolver()
    resolver.evict_individual(IndividualID("IND-000999"))
    resolver.evict_fact(FactID("FID-000999"))
    assert resolver.edge_count == 0
