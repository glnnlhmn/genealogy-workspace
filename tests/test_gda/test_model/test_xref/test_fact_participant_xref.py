"""Path: tests/test_gda/test_model/test_xref/test_fact_participant_xref.py

Atomized unit and regression test suite for FactParticipantXRef.

Operational Role:
    Verifies compound primary key minting, frozen immutability, whitespace stripping,
    and boundary validation for FactParticipantXRef.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError
from gda.enums.core import AssociatedRole
from gda.model.atom.date import DateString, EventDate
from gda.model.atom.id import FactID, IndividualID
from gda.model.xref.fact_participant_xref import FactParticipantXRef

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: FactParticipantXRef Creation & Immutability
# ==============================================================================


@pytest.mark.unit
def test_fact_participant_xref_instantiation_valid() -> None:
    """Verify valid construction with all primary and participant attributes."""
    witness = IndividualID("IND-000002")
    subject = IndividualID("IND-000001")
    fact = FactID("FID-000001")
    role = AssociatedRole.WITNESS
    event_date = EventDate(date=DateString("1875-10-14"))
    key = FactParticipantXRef.create_key(witness, role, fact)

    edge = FactParticipantXRef(
        xref_id=key,
        associated_ind_id=witness,
        fact_id=fact,
        primary_subject_id=subject,
        role=role,
        title="Marriage Solemnization",
        event_date=event_date,
    )

    assert edge.xref_id == "IND-000002::WITN::FID-000001"
    assert edge.associated_ind_id == witness
    assert edge.primary_subject_id == subject
    assert edge.fact_id == fact
    assert edge.role == AssociatedRole.WITNESS
    assert edge.title == "Marriage Solemnization"
    assert edge.event_date == event_date
    assert edge.compiled_at.value is not None


@pytest.mark.unit
def test_fact_participant_xref_create_key_deterministic() -> None:
    """Verify compound key formatting with enum and raw string role."""
    ind = IndividualID("IND-000002")
    fact = FactID("FID-000001")

    assert (
        FactParticipantXRef.create_key(ind, AssociatedRole.INFORMANT, fact)
        == "IND-000002::INFORMANT::FID-000001"
    )
    assert (
        FactParticipantXRef.create_key(ind, "GODPARENT", fact)
        == "IND-000002::GODPARENT::FID-000001"
    )


@pytest.mark.unit
def test_fact_participant_xref_frozen_immutability() -> None:
    """Verify modifying fields raises frozen instance error."""
    witness = IndividualID("IND-000002")
    subject = IndividualID("IND-000001")
    fact = FactID("FID-000001")
    edge = FactParticipantXRef(
        xref_id="KEY",
        associated_ind_id=witness,
        fact_id=fact,
        primary_subject_id=subject,
        role=AssociatedRole.CLERGY,
    )

    with pytest.raises((FrozenInstanceError, ValidationError)):
        edge.role = AssociatedRole.WITNESS  # type: ignore[misc]


# ==============================================================================
# GROUP 2: Validation Boundaries & Defensive Constraints
# ==============================================================================


@pytest.mark.unit
def test_fact_participant_xref_whitespace_stripped() -> None:
    """Verify string attributes strip leading and trailing whitespace automatically."""
    witness = IndividualID("IND-000002")
    subject = IndividualID("IND-000001")
    fact = FactID("FID-000001")

    edge = FactParticipantXRef(
        xref_id="  IND-000002::WITN::FID-000001  ",
        associated_ind_id=witness,
        fact_id=fact,
        primary_subject_id=subject,
        role=AssociatedRole.WITNESS,
        title="  Attending Witness at Concord  ",
    )

    assert edge.xref_id == "IND-000002::WITN::FID-000001"
    assert edge.title == "Attending Witness at Concord"


@pytest.mark.regression
def test_fact_participant_xref_empty_key_rejected() -> None:
    """Verify empty or whitespace-only xref_id raises ModelFormatError."""
    witness = IndividualID("IND-000002")
    subject = IndividualID("IND-000001")
    fact = FactID("FID-000001")

    with pytest.raises(ModelFormatError, match="xref_id"):
        FactParticipantXRef(
            xref_id="   ",
            associated_ind_id=witness,
            fact_id=fact,
            primary_subject_id=subject,
            role=AssociatedRole.WITNESS,
        )


@pytest.mark.regression
def test_fact_participant_xref_extra_fields_forbidden() -> None:
    """Verify Pydantic rejects undeclared extra attributes."""
    witness = IndividualID("IND-000002")
    subject = IndividualID("IND-000001")
    fact = FactID("FID-000001")

    with pytest.raises(ValidationError):
        FactParticipantXRef(  # type: ignore[call-arg]
            xref_id="KEY",
            associated_ind_id=witness,
            fact_id=fact,
            primary_subject_id=subject,
            role=AssociatedRole.WITNESS,
            forbidden_facet="INVALID",
        )
