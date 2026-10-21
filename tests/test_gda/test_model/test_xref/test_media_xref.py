"""Path: tests/test_gda/test_model/test_xref/test_media_xref.py

Atomized unit and regression test suite for MediaXRef.

Operational Role:
    Verifies UUID primary keys, entity linkage, frozen immutability,
    whitespace stripping, and boundary validation for MediaXRef.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from gda.model.atom.date import DateString, EventDate
from gda.model.atom.id import IndividualID, LocationID
from gda.model.xref.media_xref import MediaXRef

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: MediaXRef Creation & Field Invariants
# ==============================================================================


@pytest.mark.unit
def test_media_xref_instantiation_valid() -> None:
    """Verify construction with entity, media, caption, date, and UUID generation."""
    ind = IndividualID("IND-000001")
    media_uuid = uuid4()
    xref_uuid = uuid4()
    event_date = EventDate(date=DateString("1885-06-12"))

    edge = MediaXRef(
        entity_id=ind,
        media_id=media_uuid,
        xref_id=xref_uuid,
        caption="Civil War Tintype",
        date=event_date,
    )

    assert edge.entity_id == ind
    assert edge.media_id == media_uuid
    assert edge.xref_id == xref_uuid
    assert edge.caption == "Civil War Tintype"
    assert edge.date == event_date
    assert edge.compiled_at.value is not None


@pytest.mark.unit
def test_media_xref_default_uuid_minting() -> None:
    """Verify omitted xref_id automatically generates a valid UUID4."""
    loc = LocationID("LOC-000001")
    media_uuid = uuid4()

    edge = MediaXRef(
        entity_id=loc,
        media_id=media_uuid,
    )

    assert isinstance(edge.xref_id, UUID)
    assert edge.caption is None
    assert edge.date is None


@pytest.mark.unit
def test_media_xref_frozen_immutability() -> None:
    """Verify modifying fields raises frozen instance error."""
    ind = IndividualID("IND-000001")
    media_uuid = uuid4()
    edge = MediaXRef(entity_id=ind, media_id=media_uuid)

    with pytest.raises((FrozenInstanceError, ValidationError)):
        edge.caption = "Mutated Caption"  # type: ignore[misc]


# ==============================================================================
# GROUP 2: Validation Boundaries & Defensive Constraints
# ==============================================================================


@pytest.mark.unit
def test_media_xref_whitespace_stripped() -> None:
    """Verify string attributes strip leading and trailing whitespace automatically."""
    ind = IndividualID("IND-000001")
    media_uuid = uuid4()

    edge = MediaXRef(
        entity_id=ind,
        media_id=media_uuid,
        caption="  Historical Map of Bow  ",
    )

    assert edge.caption == "Historical Map of Bow"


@pytest.mark.regression
def test_media_xref_extra_fields_forbidden() -> None:
    """Verify Pydantic rejects undeclared extra attributes."""
    ind = IndividualID("IND-000001")
    media_uuid = uuid4()

    with pytest.raises(ValidationError):
        MediaXRef(  # type: ignore[call-arg]
            entity_id=ind,
            media_id=media_uuid,
            unauthorized_facet="FORBIDDEN",
        )
