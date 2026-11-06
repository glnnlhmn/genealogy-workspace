"""Path: tests/test_gda/test_model/test_entity/test_fact.py

Comprehensive test suite verifying Fact entity model contracts and mutators.

Operational Role:
    Validates evidentiary assertion lifecycles, temporal bindings (dates and periods),
    geographic anchors, participant role associations, source reference links,
    copy-on-write mutators, dictionary/JSON serialization round trips, dirty tracking
    (_dirty, is_dirty, mark_clean, mark_dirty), and defensive validation invariants
    with 100% statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError
from gda.enums.archival import NoteType
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
from gda.model.base.source import SourceReference
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import Tombstone
from gda.model.entity.fact import Fact, FactParticipant

__version__ = "1.0.0+build.17"


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Provide a valid synthetic AuditStamp fixture."""
    ts = IsoTimestamp(value="2026-10-19T12:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


@pytest.fixture
def valid_citation() -> SourceReference:
    """Provide a valid synthetic SourceReference fixture matching model contracts."""
    return SourceReference.create(
        source_id="a0000000-0000-4000-8000-000000000001",
        citation_text="Page 42, Entry 15",
    )


@pytest.fixture
def valid_fact(valid_audit: AuditStamp, valid_citation: SourceReference) -> Fact:
    """Provide a fully populated Fact fixture."""
    p1 = FactParticipant.create(
        individual_id="IND-000002",
        role=AssociatedRole.INFORMANT,
        notes="Attending neighbor",
    )
    return Fact(
        id=FactID("FID-000001"),
        audit=valid_audit,
        canonical_urn="urn:gda:fact:smith_birth_1842",
        fact_type=FactType.BIRTH,
        title="Birth of John Smith",
        primary_subject_id=IndividualID("IND-000001"),
        date=EventDate.create("1842-05-12"),
        location_id=LocationID("LOC-000010"),
        site_id=SiteID("SID-000020"),
        value="Born at home",
        description="Recorded in City Register Vol. 3",
        narrative="First child born to the family.",
        participants=[p1],
        citations=[valid_citation],
    )


# ==============================================================================
# GROUP 1: PARTICIPANT VALUE OBJECT TESTS
# ==============================================================================


@pytest.mark.regression
def test_fact_participant_factory_and_mutators() -> None:
    """Verify FactParticipant factory instantiation, copy-on-write mutators, and ordering."""
    p = FactParticipant.create(
        individual_id="IND-000001",
        role=AssociatedRole.CLERGY,
        notes="Officiating minister",
    )
    assert p.individual_id == IndividualID("IND-000001")
    assert p.role == AssociatedRole.CLERGY
    assert p.notes == "Officiating minister"
    assert str(p) == f"IND-000001 [{AssociatedRole.CLERGY.value}] (Officiating minister)"

    # update_role
    up_role = p.update_role(AssociatedRole.WITNESS)
    assert up_role is not p
    assert up_role.role == AssociatedRole.WITNESS
    assert up_role.update_role(AssociatedRole.WITNESS) is up_role

    # update_notes
    up_notes = p.update_notes("New note")
    assert up_notes is not p
    assert up_notes.notes == "New note"
    assert up_notes.update_notes("New note") is up_notes

    # ordering (different individual IDs)
    p2 = FactParticipant.create("IND-000002", AssociatedRole.WITNESS)
    assert p < p2

    # ordering tiebreaker (identical individual ID, different roles)
    p_same_id_clergy = FactParticipant.create("IND-000001", AssociatedRole.CLERGY)
    p_same_id_witness = FactParticipant.create("IND-000001", AssociatedRole.WITNESS)
    assert p_same_id_clergy < p_same_id_witness

    # Rich comparison protocol returns NotImplemented for non-participant objects
    assert p.__lt__("not-a-participant") is NotImplemented
    with pytest.raises(TypeError):
        _ = p < "not-a-participant"


@pytest.mark.regression
def test_fact_participant_role_normalization_variants() -> None:
    """Verify _normalize_role handles aliases and enum value tokens."""
    p_by_val = FactParticipant.create("IND-000001", role="WITN")
    assert p_by_val.role == AssociatedRole.WITNESS

    p_by_alias = FactParticipant.create("IND-000001", role="OFFICIAL")
    assert p_by_alias.role == AssociatedRole.OFFICIANT


@pytest.mark.integration
def test_fact_participant_serialization_round_trip() -> None:
    """Verify FactParticipant dictionary and JSON serialization round trip."""
    p = FactParticipant.create("IND-000005", AssociatedRole.INFORMANT, "Test note")
    data = p.to_dict()
    assert data == {
        "individual_id": "IND-000005",
        "role": AssociatedRole.INFORMANT.value,
        "notes": "Test note",
    }

    restored = FactParticipant.from_dict(data)
    assert restored == p

    json_str = p.to_json()
    assert FactParticipant.from_json(json_str) == p

    # to_dict without notes
    p_no_notes = FactParticipant.create("IND-000006", AssociatedRole.WITNESS)
    data_no_notes = p_no_notes.to_dict()
    assert "notes" not in data_no_notes
    assert FactParticipant.from_dict(data_no_notes).notes is None


@pytest.mark.regression
def test_fact_participant_defensive_errors() -> None:
    """Verify FactParticipant defensive error handling."""
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        FactParticipant.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'individual_id'"):
        FactParticipant.from_dict({"role": "Witness"})

    with pytest.raises(ModelFormatError, match="Failed to parse FactParticipant JSON"):
        FactParticipant.from_json("{broken-json")

    with pytest.raises(ModelFormatError, match="Cannot normalize"):
        FactParticipant.create("IND-000001", "NONEXISTENT_ROLE")


# ==============================================================================
# GROUP 2: FACT INITIALIZATION & DEFAULT ACCESSORS
# ==============================================================================


@pytest.mark.regression
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
    assert fact.is_dirty is False
    assert fact.is_individual_fact is True
    assert fact.is_family_fact is False
    assert fact.year_lower_bound is None
    assert fact.sort_key == ("IND-000001", 9999, "BIRTH", "FID-000001")


@pytest.mark.regression
def test_fact_year_lower_bound_variants(valid_fact: Fact) -> None:
    """Verify year_lower_bound extraction across EventDate and TimePeriod."""
    assert valid_fact.year_lower_bound == 1842

    # TimePeriod with start_date
    start = EventDate.create("1880-01-01")
    span = TimePeriod(start_date=start, end_date=EventDate.create("1890-01-01"))
    fact_span = valid_fact.update_date(span)
    assert fact_span.year_lower_bound == 1880

    # TimePeriod without start_date
    span_no_start = TimePeriod(end_date=EventDate.create("1890-01-01"))
    fact_no_start = valid_fact.update_date(span_no_start)
    assert fact_no_start.year_lower_bound is None


@pytest.mark.regression
def test_fact_with_time_period_and_family_subject(valid_audit: AuditStamp) -> None:
    """Verify Fact supports TimePeriod spans, FamilyID primary subjects, and year extraction."""
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
    assert fact.is_family_fact is True
    assert fact.is_individual_fact is False
    assert fact.year_lower_bound == 1910
    assert "for FAM-000001" in str(fact)
    assert fact.sort_key == ("FAM-000001", 1910, "TRAVEL", "FID-000003")


@pytest.mark.regression
def test_fact_factory_create_resolutions(valid_audit: AuditStamp) -> None:
    """Verify Fact.create resolves string IDs, string dates (line 377), objects, and auto-defaults audit."""
    # Test string date resolution (closing line 377)
    fact_str_date = Fact.create(
        fact_id="FID-000010",
        canonical_urn="urn:gda:fact:factory_test",
        fact_type="MARRIAGE",
        title="Marriage of Smith and Jones",
        primary_subject_id="FAM-000001",
        date="1865-04-12",
        location_id="LOC-000001",
        site_id="SID-000002",
        participants=[{"individual_id": "IND-000099", "role": "CLERGY"}],
        citations=[{"citation_text": "Parish Register 1865"}],
        audit=valid_audit,
    )
    assert fact_str_date.id == FactID("FID-000010")
    assert fact_str_date.fact_type == FactType.MARRIAGE
    assert fact_str_date.primary_subject_id == FamilyID("FAM-000001")
    assert fact_str_date.date == EventDate.create("1865-04-12")
    assert fact_str_date.location_id == LocationID("LOC-000001")
    assert fact_str_date.site_id == SiteID("SID-000002")
    assert fact_str_date.participant_count == 1
    assert fact_str_date.citation_count == 1

    # Fact.create passing TimePeriod instance directly
    span = TimePeriod(start_date=EventDate.create("1880-01-01"))
    fact_with_span = Fact.create(
        fact_id="FID-000012",
        canonical_urn="urn:gda:fact:period_direct",
        fact_type=FactType.RESIDENCE,
        title="Residence Period",
        primary_subject_id="IND-000001",
        date=span,
    )
    assert fact_with_span.date == span

    # Minimal create auto-defaults audit
    min_fact = Fact.create(
        fact_id="FID-000011",
        canonical_urn="urn:gda:fact:minimal_test",
        fact_type=FactType.DEATH,
        title="Death Record",
        primary_subject_id="IND-000001",
    )
    assert min_fact.audit is not None
    assert min_fact.created_at is not None


# ==============================================================================
# GROUP 3: COPY-ON-WRITE MUTATORS & STATE MANAGEMENT
# ==============================================================================


@pytest.mark.regression
def test_fact_dirty_flag_transitions(valid_fact: Fact) -> None:
    """Verify mark_dirty and mark_clean state transitions and idempotency."""
    fact = valid_fact
    assert fact.is_dirty is False

    marked_dirty = fact.mark_dirty()
    assert marked_dirty is not fact
    assert marked_dirty.is_dirty is True
    assert marked_dirty.mark_dirty() is marked_dirty

    marked_clean = marked_dirty.mark_clean()
    assert marked_clean is not marked_dirty
    assert marked_clean.is_dirty is False
    assert marked_clean.mark_clean() is marked_clean


@pytest.mark.regression
def test_fact_attribute_mutators(valid_fact: Fact) -> None:
    """Verify all field mutators produce new immutable copies and toggle dirty flag (closing line 570)."""
    fact = valid_fact

    # update_title
    up_title = fact.update_title("Birth of Jonathan Smith")
    assert up_title is not fact
    assert up_title.title == "Birth of Jonathan Smith"
    assert up_title.is_dirty is True
    assert up_title.update_title("Birth of Jonathan Smith") is up_title

    with pytest.raises(ModelFormatError, match="cannot be empty or whitespace"):
        fact.update_title("   ")

    # update_fact_type
    up_type = fact.update_fact_type("BAPTISM")
    assert up_type is not fact
    assert up_type.fact_type == FactType.BAPTISM
    assert up_type.update_fact_type(FactType.BAPTISM) is up_type

    with pytest.raises(ModelFormatError, match="Cannot normalize"):
        fact.update_fact_type("NONEXISTENT_FACT_TYPE")

    # update_date
    up_date = fact.update_date("1842-05-13")
    assert up_date is not fact
    assert str(up_date.date) == "1842-05-13"
    assert up_date.update_date(up_date.date) is up_date

    # update_location
    up_loc = fact.update_location("LOC-000099")
    assert up_loc is not fact
    assert up_loc.location_id == LocationID("LOC-000099")
    assert up_loc.update_location(LocationID("LOC-000099")) is up_loc

    # update_site
    up_site = fact.update_site("SID-000099")
    assert up_site is not fact
    assert up_site.site_id == SiteID("SID-000099")
    assert up_site.update_site(SiteID("SID-000099")) is up_site

    # update_value
    up_val = fact.update_value("Blacksmith")
    assert up_val is not fact
    assert up_val.value == "Blacksmith"
    assert up_val.update_value("Blacksmith") is up_val

    # update_description
    up_desc = fact.update_description("Extract from census")
    assert up_desc is not fact
    assert up_desc.description == "Extract from census"
    assert up_desc.update_description("Extract from census") is up_desc

    # update_narrative
    up_narr = fact.update_narrative("Full biography prose")
    assert up_narr is not fact
    assert up_narr.narrative == "Full biography prose"
    assert up_narr.update_narrative("Full biography prose") is up_narr

    # update_urn
    up_urn = fact.update_urn("urn:gda:fact:updated_slug")
    assert up_urn is not fact
    assert up_urn.canonical_urn == "urn:gda:fact:updated_slug"
    assert up_urn.update_urn("urn:gda:fact:updated_slug") is up_urn

    # Invalid URN format raises ModelFormatError (closing line 570)
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        fact.update_urn("invalid_urn_slug")


@pytest.mark.regression
def test_fact_participant_and_citation_mutators(valid_fact: Fact) -> None:
    """Verify add/remove/update mutators across participants and citations."""
    fact = valid_fact

    # add_participant
    with_p2 = fact.add_participant("IND-000003", AssociatedRole.CLERGY, "Officiant")
    assert with_p2 is not fact
    assert with_p2.participant_count == 2
    assert with_p2.add_participant("IND-000003", AssociatedRole.CLERGY, "Officiant") is with_p2

    # Duplicate individual ID with different role raises error
    with pytest.raises(ModelFormatError, match="already recorded"):
        with_p2.add_participant("IND-000003", AssociatedRole.WITNESS)

    # update_participant_role with notes
    up_part = with_p2.update_participant_role("IND-000003", AssociatedRole.WITNESS, "Updated note")
    assert up_part is not with_p2
    target_p = [p for p in up_part.participants if p.individual_id.value == "IND-000003"][0]
    assert target_p.role == AssociatedRole.WITNESS
    assert target_p.notes == "Updated note"

    # update_participant_role with notes=None
    up_part_no_notes = with_p2.update_participant_role("IND-000003", AssociatedRole.ATTENDANT)
    target_p2 = [p for p in up_part_no_notes.participants if p.individual_id.value == "IND-000003"][
        0
    ]
    assert target_p2.role == AssociatedRole.ATTENDANT
    assert target_p2.notes == "Officiant"

    # update_participant_role no-op
    assert (
        with_p2.update_participant_role("IND-000003", AssociatedRole.CLERGY, "Officiant") is with_p2
    )

    with pytest.raises(ModelFormatError, match="not found in fact participants"):
        with_p2.update_participant_role("IND-999999", AssociatedRole.WITNESS)

    # remove_participant
    rem_p = with_p2.remove_participant("IND-000003")
    assert rem_p is not with_p2
    assert rem_p.participant_count == 1
    assert rem_p.remove_participant("IND-999999") is rem_p

    # add_citation and remove_citation
    new_cite = SourceReference.create("1880 Census Merrimack")
    with_cite = fact.add_citation(new_cite)
    assert with_cite is not fact
    assert with_cite.citation_count == 2
    assert with_cite.add_citation(new_cite) is with_cite

    rem_cite = with_cite.remove_citation("1880 Census Merrimack")
    assert rem_cite is not with_cite
    assert rem_cite.citation_count == 1
    assert rem_cite.remove_citation("NONEXISTENT") is rem_cite


@pytest.mark.regression
def test_fact_update_embedded_note(valid_fact: Fact) -> None:
    """Verify Fact update_note mutator modifies embedded research notes."""
    fact = valid_fact.add_note(
        text="Initial note.",
        title="Note 1",
        note_type=NoteType.GENERAL,
        tags=["tag1"],
    ).add_note(
        text="Second note.",
        title="Note 2",
        note_type=NoteType.RESEARCH,
        tags=["tag2"],
    )
    note1_id = fact.notes[0].note_id
    note2_id = fact.notes[1].note_id

    # Update note 2 only; note 1 preserved
    updated = fact.update_note(
        note_id=note2_id,
        text="Updated second text",
        title="Updated Note 2",
        note_type=NoteType.PROOF,
        tags=["verified"],
    )
    assert updated is not fact
    assert updated.notes[0].text == "Initial note."
    assert updated.notes[1].text == "Updated second text"
    assert updated.notes[1].title == "Updated Note 2"

    # Partial updates
    up_text = fact.update_note(note_id=note1_id, text="Only text")
    assert up_text.get_note(note1_id).text == "Only text"

    up_title = fact.update_note(note_id=note1_id, title="Only title")
    assert up_title.get_note(note1_id).title == "Only title"

    up_type = fact.update_note(note_id=note1_id, note_type=NoteType.DISCREPANCY)
    assert up_type.get_note(note1_id).note_type == NoteType.DISCREPANCY

    up_tags = fact.update_note(note_id=note1_id, tags=["new"])
    assert up_tags.get_note(note1_id).tags == ["new"]

    assert fact.update_note("NOT-999999", text="No-op") is fact


# ==============================================================================
# GROUP 4: SERIALIZATION & ROUND TRIPS
# ==============================================================================


@pytest.mark.integration
def test_fact_serialization_round_trip(valid_fact: Fact) -> None:
    """Verify Fact dictionary and JSON serialization round trip."""
    data = valid_fact.to_dict()

    assert data["id"] == "FID-000001"
    assert data["canonical_urn"] == "urn:gda:fact:smith_birth_1842"
    assert data["fact_type"] == "BIRTH"
    assert data["primary_subject_id"] == "IND-000001"
    assert data["date"] == {"date": "1842-05-12"}
    assert data["location_id"] == "LOC-000010"
    assert data["site_id"] == "SID-000020"
    assert len(data["participants"]) == 1
    assert len(data["citations"]) == 1

    restored = Fact.from_dict(data)
    assert restored.id == valid_fact.id
    assert restored.canonical_urn == valid_fact.canonical_urn
    assert restored.fact_type == valid_fact.fact_type
    assert restored.primary_subject_id == valid_fact.primary_subject_id
    assert restored.date == valid_fact.date
    assert restored.location_id == valid_fact.location_id
    assert restored.site_id == valid_fact.site_id
    assert restored.participant_count == 1
    assert restored.citation_count == 1

    json_str = valid_fact.to_json()
    assert Fact.from_json(json_str).id == valid_fact.id


@pytest.mark.integration
def test_fact_serialization_with_time_period_and_minimal_to_dict() -> None:
    """Verify Fact serialization with TimePeriod and minimal to_dict."""
    fact_period = Fact.create(
        fact_id="FID-000020",
        canonical_urn="urn:gda:fact:period_test",
        fact_type="RESIDENCE",
        title="Residence in Bow",
        primary_subject_id="IND-000001",
        date={"start_date": "1850-01-01", "end_date": "1860-12-31"},
    )
    data_period = fact_period.to_dict()
    assert data_period["date"]["start_date"] == "1850-01-01"
    assert data_period["date"]["end_date"] == "1860-12-31"

    # Minimal fact without date, location, site, value, description, narrative
    fact_min = Fact.create(
        fact_id="FID-000021",
        canonical_urn="urn:gda:fact:min_dict_test",
        fact_type="CENSUS",
        title="Census Entry",
        primary_subject_id="IND-000001",
    )
    data_min = fact_min.to_dict()
    assert "date" not in data_min
    assert "location_id" not in data_min
    assert "site_id" not in data_min
    assert "value" not in data_min
    assert "description" not in data_min
    assert "narrative" not in data_min


@pytest.mark.integration
def test_fact_from_dict_minimal_and_tombstone() -> None:
    """Verify Fact.from_dict with minimal payload and tombstone variants."""
    data_tomb = {
        "id": "FID-000030",
        "canonical_urn": "urn:gda:fact:tomb_test",
        "fact_type": "DEATH",
        "title": "Death Assertion",
        "primary_subject_id": "IND-000001",
        "tombstone": {
            "is_deprecated": True,
            "deprecated_at": "2026-10-20T12:00:00Z",
            "superseded_by": "FID-000031",
        },
    }
    restored = Fact.from_dict(data_tomb)
    assert restored.is_deprecated is True
    assert restored.superseded_by == FactID("FID-000031")

    # Minimal without tombstone or audit
    data_min = {
        "id": "FID-000032",
        "canonical_urn": "urn:gda:fact:min_test",
        "fact_type": "CENSUS",
        "title": "1880 Census Entry",
        "primary_subject_id": "FAM-000001",
    }
    restored_min = Fact.from_dict(data_min)
    assert restored_min.is_deprecated is False
    assert restored_min.audit is not None


@pytest.mark.regression
def test_fact_deserialization_defensive_errors() -> None:
    """Verify Fact deserialization error boundaries."""
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        Fact.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'id'"):
        Fact.from_dict({"title": "No ID"})

    with pytest.raises(ModelFormatError, match="Fact requires 'fact_type'"):
        Fact.from_dict({"id": "FID-000001", "canonical_urn": "urn:x"})

    with pytest.raises(ModelFormatError, match="Failed to parse Fact JSON string"):
        Fact.from_json("{broken json")

    with pytest.raises(TypeError, match="Cannot resolve participant from payload"):
        Fact.create(
            fact_id="FID-000001",
            canonical_urn="urn:gda:fact:bad_part",
            fact_type="BIRTH",
            title="Bad Part",
            primary_subject_id="IND-000001",
            participants=[12345],  # type: ignore[list-item]
        )

    with pytest.raises(TypeError, match="Cannot resolve citation from payload"):
        Fact.create(
            fact_id="FID-000001",
            canonical_urn="urn:gda:fact:bad_cite",
            fact_type="BIRTH",
            title="Bad Cite",
            primary_subject_id="IND-000001",
            citations=[12345],  # type: ignore[list-item]
        )


# ==============================================================================
# GROUP 5: DEFENSIVE BOUNDARIES & RELATIONAL INTEGRITY
# ==============================================================================


@pytest.mark.regression
def test_fact_invalid_id_type(valid_audit: AuditStamp) -> None:
    """Verify ValidationError when id is not an instance of FactID."""
    with pytest.raises((ValidationError, TypeError)):
        Fact(
            id="FID-000001",  # type: ignore[arg-type]
            audit=valid_audit,
            canonical_urn="urn:gda:fact:bad_id",
            fact_type=FactType.BIRTH,
            title="Bad ID Type",
            primary_subject_id=IndividualID(value="IND-000001"),
        )


@pytest.mark.regression
def test_fact_post_init_id_type_defensive(valid_fact: Fact) -> None:
    """Verify __post_init__ raises TypeError when self.id is mutated to non-FactID."""
    object.__setattr__(valid_fact, "id", "NOT_A_FACT_ID")
    with pytest.raises(TypeError, match="must be an instance of FactID"):
        valid_fact.__post_init__()


@pytest.mark.regression
def test_fact_post_init_id_pattern_defensive(valid_fact: Fact) -> None:
    """Verify __post_init__ raises ModelFormatError when raw_id violates regex."""

    class MalformedFactID(FactID):
        def __init__(self, value: str) -> None:
            object.__setattr__(self, "value", value)
            object.__setattr__(self, "expected_prefix", "FID")

    object.__setattr__(valid_fact, "id", MalformedFactID("BAD-123"))
    with pytest.raises(ModelFormatError, match="Invalid FactID format"):
        valid_fact.__post_init__()


@pytest.mark.regression
def test_fact_empty_title_raises_error(valid_audit: AuditStamp) -> None:
    """Verify Fact raises ModelFormatError when title is empty or whitespace."""
    with pytest.raises(ModelFormatError, match="Fact 'title' cannot be empty or whitespace"):
        Fact(
            id=FactID("FID-000001"),
            audit=valid_audit,
            canonical_urn="urn:gda:fact:empty_title",
            fact_type=FactType.BIRTH,
            title="   ",
            primary_subject_id=IndividualID("IND-000001"),
        )

    with pytest.raises(ModelFormatError, match="Fact 'title' cannot be empty or whitespace"):
        Fact.create(
            fact_id="FID-000001",
            canonical_urn="urn:gda:fact:empty_title",
            fact_type=FactType.BIRTH,
            title="   ",
            primary_subject_id="IND-000001",
        )


@pytest.mark.regression
def test_fact_invalid_subject_type_raises_error(valid_audit: AuditStamp) -> None:
    """Verify Fact raises TypeError when primary_subject_id is neither IndividualID nor FamilyID."""
    fact = Fact.create(
        fact_id="FID-000001",
        canonical_urn="urn:gda:fact:test_subj",
        fact_type="BIRTH",
        title="Test Subj",
        primary_subject_id="IND-000001",
        audit=valid_audit,
    )
    object.__setattr__(fact, "primary_subject_id", SourceID("a0000000-0000-4000-8000-000000000001"))
    with pytest.raises(TypeError, match="must be IndividualID or FamilyID"):
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
    tombstone = Tombstone[FactID](
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
def test_fact_superseded_by_other_allowed(valid_audit: AuditStamp) -> None:
    """Verify tombstone with valid superseded_by does not raise error."""
    fid = FactID(value="FID-000001")
    other_fid = FactID(value="FID-000002")
    tombstone = Tombstone[FactID](
        is_deprecated=True,
        deprecated_at=IsoTimestamp.now_utc(),
        superseded_by=other_fid,
    )
    fact = Fact(
        id=fid,
        audit=valid_audit,
        canonical_urn="urn:gda:fact:smith_birth_1842",
        fact_type=FactType.BIRTH,
        title="Superseded",
        primary_subject_id=IndividualID(value="IND-000001"),
        tombstone=tombstone,
    )
    assert fact.is_deprecated is True
    assert fact.superseded_by == other_fid


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

    # Mutator guard
    fact = Fact.create(
        fact_id="FID-000001",
        canonical_urn="urn:gda:fact:smith_will_1890",
        fact_type=FactType.WILL,
        title="Will Signing",
        primary_subject_id=subject,
        audit=valid_audit,
    )
    with pytest.raises(ModelFormatError, match="Primary subject cannot also be listed"):
        fact.add_participant(subject)


# ==============================================================================
# GROUP 6: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.regression
def test_fact_immutability(valid_fact: Fact) -> None:
    """Verify Fact instances are frozen and immutable."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        valid_fact.title = "Mutated"  # type: ignore[misc]

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        valid_fact.participants = []  # type: ignore[misc]


@pytest.mark.regression
def test_fact_introspection(valid_fact: Fact) -> None:
    """Verify .help() introspection renders member directory on Fact."""
    help_text = valid_fact.help(as_str=True)
    assert help_text is not None
    assert "=== Fact Public Directory ===" in help_text
    assert "update_title" in help_text
    assert "update_fact_type" in help_text
    assert "update_date" in help_text
    assert "update_location" in help_text
    assert "update_site" in help_text
    assert "update_value" in help_text
    assert "update_description" in help_text
    assert "update_narrative" in help_text
    assert "update_urn" in help_text
    assert "add_participant" in help_text
    assert "remove_participant" in help_text
    assert "update_participant_role" in help_text
    assert "add_citation" in help_text
    assert "remove_citation" in help_text
    assert "to_dict" in help_text
    assert "from_dict" in help_text
    assert "to_json" in help_text
    assert "from_json" in help_text
    assert "is_dirty" in help_text
    assert "is_family_fact" in help_text
    assert "is_individual_fact" in help_text
    assert "year_lower_bound" in help_text
    assert "sort_key" in help_text
