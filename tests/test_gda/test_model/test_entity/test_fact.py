"""Path: tests/test_gda/test_model/test_entity/test_fact.py

Comprehensive test suite verifying Fact entity model contracts and invariants.

Operational Role:
    Validates evidentiary assertion lifecycles, temporal bindings (dates and periods),
    geographic anchors, participant role associations, source reference links,
    and defensive validation invariants.

Test Structure & Protocol:
    - Atomized tests: Enforces 1:1 behavioral contract verification per test function.
    - Fully decorated: Explicit enumeration of pytest markers (unit, regression).
    - Dependencies: Synthetic fixtures and isolated in-memory model instances.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError
from gda.enums.core import AssociatedRole, FactType
from gda.model.atom.date import DateString, EventDate, IsoTimestamp
from gda.model.atom.id import (
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    SiteID,
    SourceID,
)
from gda.model.base.audit import AuditStamp
from gda.model.base.source_reference import SourceReference
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import TombstoneRecord
from gda.model.entity.fact import Fact, FactParticipant

__version__ = "1.0.0+build.11"


# ==============================================================================
# FIXTURES
# Note: Handcrafted synthetic baselines for temporal stamps and citations.
# ==============================================================================


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Provide a valid synthetic AuditStamp fixture."""
    ts = IsoTimestamp(value="2026-10-19T12:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


@pytest.fixture
def valid_citation() -> SourceReference:
    """Provide a valid synthetic SourceReference fixture matching model contracts."""
    return SourceReference(
        source_id=SourceID(value="a0000000-0000-4000-8000-000000000001"),
        citation_text="Page 42, Entry 15",
    )


# ==============================================================================
# GROUP 1: PARTICIPANT VALUE OBJECT TESTS
# Note: Verification of FactParticipant initialization, defaults, and string formats.
# ==============================================================================


@pytest.mark.unit
def test_fact_participant_defaults() -> None:
    """Verify FactParticipant minimal instantiation defaults to AssociatedRole.WITNESS."""
    ind_id = IndividualID(value="IND-000001")
    p = FactParticipant(individual_id=ind_id)
    assert p.individual_id == ind_id
    assert p.role == AssociatedRole.WITNESS
    assert p.notes is None
    assert str(p) == f"IND-000001 [{AssociatedRole.WITNESS.value}]"


@pytest.mark.unit
def test_fact_participant_with_notes() -> None:
    """Verify FactParticipant string rendering with explicit role and notes."""
    ind_id = IndividualID(value="IND-000002")
    p = FactParticipant(
        individual_id=ind_id,
        role=AssociatedRole.CLERGY,
        notes="Officiating minister",
    )
    assert p.role == AssociatedRole.CLERGY
    assert (
        str(p) == f"IND-000002 [{AssociatedRole.CLERGY.value}] (Officiating minister)"
    )


# ==============================================================================
# GROUP 2: FACT INITIALIZATION & DEFAULT ACCESSORS
# Note: Verification of field propagation, defaults, and accessor properties.
# ==============================================================================


@pytest.mark.unit
def test_fact_minimal_instantiation(valid_audit: AuditStamp) -> None:
    """Verify Fact minimal instantiation defaults and collection initializers."""
    fact = Fact(
        id=FactID(value="FID-000001"),
        audit=valid_audit,
        canonical_urn="urn:gda:fact:smith_birth_1842",
        fact_type=FactType.BIRTH,
        title="Birth of John Smith",
        primary_subject_id=IndividualID(value="IND-000001"),
    )
    assert fact.id.value == "FID-000001"
    assert fact.fact_type == FactType.BIRTH
    assert fact.title == "Birth of John Smith"
    assert fact.primary_subject_id == IndividualID(value="IND-000001")
    assert fact.date is None
    assert fact.location_id is None
    assert fact.site_id is None
    assert fact.value is None
    assert fact.description is None
    assert fact.narrative is None
    assert fact.participants == []
    assert fact.participant_ids == []
    assert fact.participant_count == 0
    assert fact.citations == []
    assert fact.citation_count == 0
    assert fact.is_deprecated is False
    assert (
        str(fact)
        == f"Fact [{FactType.BIRTH.value}] 'Birth of John Smith' for IND-000001 (FID-000001)"
    )


@pytest.mark.unit
def test_fact_full_specification(
    valid_audit: AuditStamp,
    valid_citation: SourceReference,
) -> None:
    """Verify Fact instantiation with all temporal, geographic, and narrative fields."""
    ev_date = EventDate(date=DateString(value="1880-06-15"))
    loc_id = LocationID(value="LOC-000010")
    sit_id = SiteID(value="SID-000020")
    p1 = FactParticipant(
        individual_id=IndividualID(value="IND-000002"),
        role=AssociatedRole.INFORMANT,
    )

    fact = Fact(
        id=FactID(value="FID-000002"),
        audit=valid_audit,
        canonical_urn="urn:gda:fact:smith_death_1880",
        fact_type=FactType.DEATH,
        title="Death of John Smith",
        primary_subject_id=IndividualID(value="IND-000001"),
        date=ev_date,
        location_id=loc_id,
        site_id=sit_id,
        value="Heart Failure",
        description="Recorded in City Register Vol. 3",
        narrative="Passed away peacefully at home surrounded by family.",
        participants=[p1],
        citations=[valid_citation],
    )
    assert fact.date == ev_date
    assert fact.location_id == loc_id
    assert fact.site_id == sit_id
    assert fact.value == "Heart Failure"
    assert fact.participant_count == 1
    assert fact.participant_ids == [IndividualID(value="IND-000002")]
    assert fact.citation_count == 1
    assert "on 1880-06-15" in str(fact)


@pytest.mark.unit
def test_fact_with_time_period_and_family_subject(valid_audit: AuditStamp) -> None:
    """Verify Fact supports TimePeriod spans and FamilyID primary subjects."""
    start = EventDate(date=DateString(value="1910-07-01"))
    end = EventDate(date=DateString(value="1910-07-20"))
    span = TimePeriod(start_date=start, end_date=end)

    fact = Fact(
        id=FactID(value="FID-000003"),
        audit=valid_audit,
        canonical_urn="urn:gda:fact:smith_vacation_1910",
        fact_type=FactType.TRAVEL,
        title="Summer Vacation in White Mountains",
        primary_subject_id=FamilyID(value="FAM-000001"),
        date=span,
    )
    assert fact.primary_subject_id == FamilyID(value="FAM-000001")
    assert fact.date == span
    assert "for FAM-000001" in str(fact)


# ==============================================================================
# GROUP 3: DEFENSIVE INVARIANTS & INTEGRITY GUARDS
# Note: Verification of validation boundaries, regex constraints, and self-checks.
# ==============================================================================


@pytest.mark.regression
def test_fact_invalid_id_type(valid_audit: AuditStamp) -> None:
    """Verify ValidationError when id is not an instance of FactID."""
    with pytest.raises(ValidationError):
        Fact(
            id="FID-000001",  # type: ignore[arg-type]
            audit=valid_audit,
            canonical_urn="urn:gda:fact:bad_id",
            fact_type=FactType.BIRTH,
            title="Bad ID Type",
            primary_subject_id=IndividualID(value="IND-000001"),
        )


@pytest.mark.regression
def test_fact_post_init_id_type_defensive(valid_audit: AuditStamp) -> None:
    """Verify __post_init__ raises TypeError when self.id is mutated to non-FactID."""
    fact = Fact(
        id=FactID(value="FID-000001"),
        audit=valid_audit,
        canonical_urn="urn:gda:fact:test_type",
        fact_type=FactType.BIRTH,
        title="Test Type",
        primary_subject_id=IndividualID(value="IND-000001"),
    )
    object.__setattr__(fact, "id", "NOT_A_FACT_ID")
    with pytest.raises(TypeError, match="must be an instance of FactID"):
        fact.__post_init__()


@pytest.mark.regression
def test_fact_post_init_id_pattern_defensive(valid_audit: AuditStamp) -> None:
    """Verify __post_init__ raises ModelFormatError when raw_id violates regex."""

    class MalformedFactID(FactID):
        def __init__(self, value: str) -> None:
            object.__setattr__(self, "value", value)

    fact = Fact(
        id=FactID(value="FID-000001"),
        audit=valid_audit,
        canonical_urn="urn:gda:fact:test_pattern",
        fact_type=FactType.BIRTH,
        title="Test Pattern",
        primary_subject_id=IndividualID(value="IND-000001"),
    )
    object.__setattr__(fact, "id", MalformedFactID("BAD-123"))
    with pytest.raises(ModelFormatError, match="Invalid FactID format"):
        fact.__post_init__()


@pytest.mark.regression
def test_fact_invalid_urn_format(valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when canonical_urn syntax is malformed."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        Fact(
            id=FactID(value="FID-000001"),
            audit=valid_audit,
            canonical_urn="urn:gda:invalid:fact:slug!",
            fact_type=FactType.BIRTH,
            title="Invalid URN",
            primary_subject_id=IndividualID(value="IND-000001"),
        )


@pytest.mark.regression
def test_fact_self_supersession_forbidden(valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when tombstone supersedes self."""
    fid = FactID(value="FID-000001")
    tombstone = TombstoneRecord[FactID](
        is_deprecated=True,
        deprecated_at=IsoTimestamp.now_utc(),
        superseded_by=fid,
    )
    with pytest.raises(ModelFormatError, match="Fact cannot be superseded by itself"):
        Fact(
            id=fid,
            audit=valid_audit,
            canonical_urn="urn:gda:fact:smith_birth_1842",
            fact_type=FactType.BIRTH,
            title="Self Superseded",
            primary_subject_id=IndividualID(value="IND-000001"),
            tombstone=tombstone,
        )


@pytest.mark.regression
def test_fact_duplicate_participants_forbidden(valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when the same individual appears multiple times in participants."""
    ind = IndividualID(value="IND-000002")
    p1 = FactParticipant(individual_id=ind, role=AssociatedRole.WITNESS)
    p2 = FactParticipant(individual_id=ind, role=AssociatedRole.CLERGY)

    with pytest.raises(
        ModelFormatError, match="Duplicate individual entries found in participants"
    ):
        Fact(
            id=FactID(value="FID-000001"),
            audit=valid_audit,
            canonical_urn="urn:gda:fact:smith_marriage_1870",
            fact_type=FactType.MARRIAGE,
            title="Marriage Ceremony",
            primary_subject_id=FamilyID(value="FAM-000001"),
            participants=[p1, p2],
        )


@pytest.mark.regression
def test_fact_primary_subject_cannot_be_participant(valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when primary subject is also listed in participants."""
    subject = IndividualID(value="IND-000001")
    p1 = FactParticipant(individual_id=subject, role=AssociatedRole.WITNESS)

    with pytest.raises(ModelFormatError, match="Primary subject cannot also be listed"):
        Fact(
            id=FactID(value="FID-000001"),
            audit=valid_audit,
            canonical_urn="urn:gda:fact:smith_will_1890",
            fact_type=FactType.WILL,
            title="Will Signing",
            primary_subject_id=subject,
            participants=[p1],
        )
