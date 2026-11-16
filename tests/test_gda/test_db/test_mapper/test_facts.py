"""Path: tests/test_gda/test_db/test_mapper/test_facts.py

Unit and regression verification suite for FactRowMapper.

Operational Role:
    1:1 verification suite for src/gda/db/mapper/facts.py. Validates lossless
    round-trip mapping for Fact entities (with IndividualID or FamilyID
    subjects, EventDate or TimePeriod or None dates, participants, and
    citations) and EntityMappingError boundaries.
"""

from __future__ import annotations

import pytest

import gda.db.mapper.facts as facts_mod
from gda.core.enums.core import AssociatedRole, FactType
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.facts import FactRowMapper
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.source import SourceReference
from gda.model.base.tombstone import Tombstone
from gda.model.entity.fact import Fact, FactParticipant

__version__ = "1.0.0+build.1"


def _make_audit() -> AuditStamp:
    now = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=now, updated_at=now)


@pytest.mark.unit
def test_facts_mapper_dunder_all() -> None:
    """Verify gda.db.mapper.facts.__all__ is sorted."""
    assert facts_mod.__all__ == ["FactRowMapper"]


@pytest.mark.integration
def test_fact_row_mapper_round_trip_variants() -> None:
    """Verify FactRowMapper round-trips EventDate, TimePeriod, and undated Fact entities."""
    audit = _make_audit()
    cite = SourceReference.create("Town Marriage Records, Vol 1, p. 42")
    part = FactParticipant.create("IND-000002", AssociatedRole.SPOUSE)

    fact = Fact.create(
        fact_id="FID-000001",
        canonical_urn="urn:gda:fact:smith_marriage_1865",
        fact_type=FactType.MARRIAGE,
        title="Marriage Ceremony",
        primary_subject_id="IND-000001",
        date="1865-06-15",
        location_id="LOC-000001",
        site_id="SID-000001",
        value="Ceremony solemnized by Rev. Smith",
        participants=[part],
        citations=[cite],
        audit=audit,
        tombstone=Tombstone(
            is_deprecated=True,
            deprecated_at=audit.updated_at,
            superseded_by=FactID("FID-000002"),
        ),
    )

    mapper = FactRowMapper()
    row_data = mapper.to_row(fact)
    assert row_data["fact_year"] == 1865
    assert row_data["fact_date_sort"] == "1865-06-15"
    assert mapper.from_row(row_data) == fact

    period = TimePeriod(
        start_date=EventDate.create("1880-06-01"),
        end_date=EventDate.create("1880-06-30"),
    )
    fact_period = Fact.create(
        fact_id="FID-000002",
        canonical_urn="urn:gda:fact:census_1880",
        fact_type=FactType.CENSUS,
        title="1880 Federal Census",
        primary_subject_id="FAM-000001",
        date=period,
        site_id="SID-000002",
        audit=audit,
    )
    row_period = mapper.to_row(fact_period)
    assert row_period["fact_year"] == 1880
    assert row_period["fact_date_sort"] == "1880-06-01"
    assert mapper.from_row(row_period) == fact_period

    fact_undated = Fact.create(
        fact_id="FID-000003",
        canonical_urn="urn:gda:fact:undated_1",
        fact_type=FactType.OCCUPATION,
        title="Blacksmith",
        primary_subject_id="IND-000001",
        date=None,
        audit=audit,
    )
    row_undated = mapper.to_row(fact_undated)
    row_undated["participants_json"] = None
    row_undated["citations_json"] = None
    assert row_undated["fact_date_sort"] is None
    assert mapper.from_row(row_undated) == fact_undated


@pytest.mark.regression
def test_fact_row_mapper_corrupt_row_raises_error() -> None:
    """Verify FactRowMapper raises EntityMappingError on invalid row."""
    with pytest.raises(EntityMappingError, match="Failed to map row to Fact"):
        FactRowMapper().from_row({"id": None})
