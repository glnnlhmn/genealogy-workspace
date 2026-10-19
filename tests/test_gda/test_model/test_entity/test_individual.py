"""Path: tests/test_gda/test_model/test_entity/test_individual.py

Comprehensive test suite verifying Individual entity model contracts and invariants.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.model.atom.date import (
    DateModifier,
    DateString,
    EventDate,
    EventDateRange,
    IsoTimestamp,
)
from gda.model.atom.id import IndividualID, LocationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import CanonicalName, HistoricalName, NameStatus
from gda.model.base.tombstone import TombstoneRecord
from gda.model.entity.individual import Individual, _extract_year_lower_bound

__version__ = "1.0.0+build.7"


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def valid_audit() -> AuditStamp:
    ts = IsoTimestamp(value="2026-10-18T12:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


@pytest.fixture
def valid_name() -> CanonicalName:
    return CanonicalName(
        raw_name="Johnathan Edward Smith",
        given="Johnathan",
        middle="Edward",
        surname="Smith",
    )


@pytest.fixture
def point_birth_date() -> EventDate:
    return EventDate(date=DateString(value="1842-05-12"))


@pytest.fixture
def point_death_date() -> EventDate:
    return EventDate(date=DateString(value="1910-10-15"))


@pytest.fixture
def range_death_date() -> EventDateRange:
    start = EventDate(date=DateString(value="1910-01-01"))
    end = EventDate(date=DateString(value="1912-12-31"))
    return EventDateRange(start_date=start, end_date=end, modifier=DateModifier.BETWEEN)


@pytest.fixture
def valid_individual(
    valid_audit: AuditStamp,
    valid_name: CanonicalName,
    point_birth_date: EventDate,
    range_death_date: EventDateRange,
) -> Individual:
    return Individual(
        id=IndividualID(value="IND-000101"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_johnathan_1842",
        sex="M",
        birth_date=point_birth_date,
        death_date=range_death_date,
        birth_place_id=LocationID(value="LOC-000010"),
        death_place_id=SiteID(value="SID-000020"),
    )


# ==============================================================================
# GROUP 1: INITIALIZATION & BASELINE BEHAVIOR
# ==============================================================================


@pytest.mark.unit
def test_individual_init_minimal_defaults(
    valid_audit: AuditStamp, valid_name: CanonicalName
) -> None:
    """Verify minimal instantiation defaults and unpopulated fields."""
    ind = Individual(
        id=IndividualID(value="IND-000001"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_johnathan_000001",
    )
    assert ind.id.value == "IND-000001"
    assert ind.sex == "U"
    assert ind.birth_date is None
    assert ind.death_date is None
    assert ind.birth_place_id is None
    assert ind.death_place_id is None
    assert ind.is_deceased is True
    assert ind.historical_names == []
    assert ind.alternate_names == []
    assert ind.notes == []
    assert ind.is_deprecated is False
    assert ind.birth_year is None
    assert ind.death_year is None
    assert ind.approximate_age is None


@pytest.mark.unit
def test_individual_flexible_place_ids(
    valid_audit: AuditStamp, valid_name: CanonicalName
) -> None:
    """Verify birth_place_id and death_place_id accept both LocationID and SiteID."""
    loc_id = LocationID(value="LOC-000001")
    sid_id = SiteID(value="SID-000002")

    ind = Individual(
        id=IndividualID(value="IND-000001"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_000001",
        birth_place_id=sid_id,
        death_place_id=loc_id,
    )
    assert ind.birth_place_id == sid_id
    assert ind.death_place_id == loc_id


@pytest.mark.unit
def test_individual_str_representation_range_death(
    valid_individual: Individual,
) -> None:
    """Verify string formatting renders vitals with an EventDateRange death date."""
    expected = (
        "Johnathan Edward Smith [M] (b. 1842-05-12, "
        "d. BET 1910-01-01 AND 1912-12-31) (IND-000101)"
    )
    assert str(valid_individual) == expected


@pytest.mark.unit
def test_individual_str_representation_point_death(
    valid_audit: AuditStamp,
    valid_name: CanonicalName,
    point_birth_date: EventDate,
    point_death_date: EventDate,
) -> None:
    """Verify string formatting renders vitals with a point EventDate death date."""
    ind = Individual(
        id=IndividualID(value="IND-000102"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_johnathan_1842",
        sex="M",
        birth_date=point_birth_date,
        death_date=point_death_date,
    )
    assert (
        str(ind)
        == "Johnathan Edward Smith [M] (b. 1842-05-12, d. 1910-10-15) (IND-000102)"
    )


@pytest.mark.unit
def test_individual_str_living(
    valid_audit: AuditStamp, valid_name: CanonicalName, point_birth_date: EventDate
) -> None:
    """Verify string formatting renders living status when is_deceased is False."""
    ind = Individual(
        id=IndividualID(value="IND-000002"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_living_000002",
        sex="F",
        birth_date=point_birth_date,
        is_deceased=False,
    )
    assert str(ind) == "Johnathan Edward Smith [F] (b. 1842-05-12, living) (IND-000002)"


@pytest.mark.unit
def test_individual_str_deceased_unknown_death(
    valid_audit: AuditStamp, valid_name: CanonicalName, point_birth_date: EventDate
) -> None:
    """Verify string formatting renders 'd. unk' when deceased but death_date is None."""
    ind = Individual(
        id=IndividualID(value="IND-000003"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_000003",
        birth_date=point_birth_date,
        is_deceased=True,
    )
    assert str(ind) == "Johnathan Edward Smith [U] (b. 1842-05-12, d. unk) (IND-000003)"


@pytest.mark.unit
def test_individual_str_no_dates(
    valid_audit: AuditStamp, valid_name: CanonicalName
) -> None:
    """Verify string formatting when no dates are present."""
    ind = Individual(
        id=IndividualID(value="IND-000004"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_000004",
    )
    assert str(ind) == "Johnathan Edward Smith [U] (IND-000004)"


# ==============================================================================
# GROUP 2: YEARS, AGE CALCULATION & REGISTER SORTING
# ==============================================================================


@pytest.mark.unit
def test_individual_year_extraction_and_age(valid_individual: Individual) -> None:
    """Verify lower-bound year extraction and approximate age calculation."""
    assert valid_individual.display_name == "Johnathan Edward Smith"
    assert valid_individual.birth_year == 1842
    assert valid_individual.death_year == 1910
    assert valid_individual.approximate_age == 68


@pytest.mark.unit
def test_extract_year_lower_bound_helper() -> None:
    """Verify standalone _extract_year_lower_bound branches directly."""
    assert _extract_year_lower_bound(None) is None

    unparseable = EventDate(date=DateString(value="circa medieval"))
    assert _extract_year_lower_bound(unparseable) is None

    valid_point = EventDate(date=DateString(value="1776-07-04"))
    assert _extract_year_lower_bound(valid_point) == 1776


@pytest.mark.unit
def test_individual_approximate_age_missing_one_bound(
    valid_audit: AuditStamp, valid_name: CanonicalName, point_birth_date: EventDate
) -> None:
    """Verify approximate_age evaluates to None if only birth_date is present."""
    ind = Individual(
        id=IndividualID(value="IND-000005"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_000005",
        birth_date=point_birth_date,
    )
    assert ind.birth_year == 1842
    assert ind.death_year is None
    assert ind.approximate_age is None


@pytest.mark.unit
def test_individual_register_sort_key(
    valid_audit: AuditStamp,
    valid_individual: Individual,
) -> None:
    """Verify deterministic register sort key uses lower-bound year and tiebreakers."""
    assert valid_individual.sort_key == ("smith", "johnathan", 1842, "IND-000101")

    older_smith = Individual(
        id=IndividualID(value="IND-000090"),
        audit=valid_audit,
        name=CanonicalName(raw_name="Aaron Smith", given="Aaron", surname="Smith"),
        canonical_urn="urn:gda:ind:smith_aaron_000090",
        birth_date=EventDate(date=DateString(value="1820-01-01")),
    )
    undated_smith = Individual(
        id=IndividualID(value="IND-000095"),
        audit=valid_audit,
        name=CanonicalName(raw_name="Zachary Smith", given="Zachary", surname="Smith"),
        canonical_urn="urn:gda:ind:smith_zachary_000095",
    )

    records = [undated_smith, valid_individual, older_smith]
    sorted_records = sorted(records, key=lambda ind: ind.sort_key)

    assert sorted_records == [older_smith, valid_individual, undated_smith]
    assert undated_smith.sort_key == ("smith", "zachary", 9999, "IND-000095")


@pytest.mark.unit
def test_individual_sort_key_missing_name_components(valid_audit: AuditStamp) -> None:
    """Verify sort_key handles None surname or given gracefully."""
    ind = Individual(
        id=IndividualID(value="IND-000099"),
        audit=valid_audit,
        name=CanonicalName(raw_name="Anonymous"),
        canonical_urn="urn:gda:ind:anonymous_000099",
    )
    assert ind.sort_key == ("", "", 9999, "IND-000099")


# ==============================================================================
# GROUP 3: DEFENSIVE INVARIANTS & INTEGRITY BOUNDARIES
# ==============================================================================


@pytest.mark.regression
def test_individual_invalid_id_type(
    valid_audit: AuditStamp, valid_name: CanonicalName
) -> None:
    """Verify ValidationError when id is not an instance of AtomID/IndividualID."""
    with pytest.raises(ValidationError):
        Individual(
            id="IND-000001",  # type: ignore[arg-type]
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_000001",
        )


@pytest.mark.regression
def test_individual_post_init_id_type_defensive(valid_individual: Individual) -> None:
    """Verify __post_init__ raises TypeError when self.id is not an IndividualID (line 96)."""
    object.__setattr__(valid_individual, "id", "NOT_AN_INDIVIDUAL_ID")
    with pytest.raises(TypeError, match="must be an instance of IndividualID"):
        valid_individual.__post_init__()


@pytest.mark.regression
def test_individual_post_init_id_pattern_defensive(
    valid_individual: Individual,
) -> None:
    """Verify __post_init__ raises ModelFormatError when raw_id violates pattern (line 102)."""

    class MalformedIndividualID(IndividualID):
        """Bypass subclass simulating invalid prefix format."""

        def __init__(self, value: str) -> None:
            object.__setattr__(self, "value", value)

    object.__setattr__(valid_individual, "id", MalformedIndividualID("BAD-123"))
    with pytest.raises(ModelFormatError, match="Invalid IndividualID format"):
        valid_individual.__post_init__()


@pytest.mark.regression
def test_individual_invalid_urn_format(
    valid_audit: AuditStamp, valid_name: CanonicalName
) -> None:
    """Verify ModelFormatError when canonical_urn syntax is malformed."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        Individual(
            id=IndividualID(value="IND-000001"),
            audit=valid_audit,
            name=valid_name,
            canonical_urn="invalid:urn:pattern",
        )


@pytest.mark.regression
def test_individual_self_supersession_forbidden(
    valid_audit: AuditStamp, valid_name: CanonicalName
) -> None:
    """Verify ModelFormatError when tombstone supersedes self."""
    ind_id = IndividualID(value="IND-000001")
    tombstone = TombstoneRecord[IndividualID](
        is_deprecated=True,
        deprecated_at=IsoTimestamp.now_utc(),
        superseded_by=ind_id,
    )
    with pytest.raises(
        ModelFormatError, match="Individual cannot be superseded by itself"
    ):
        Individual(
            id=ind_id,
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_000001",
            tombstone=tombstone,
        )


@pytest.mark.regression
def test_individual_living_cannot_possess_death_data(
    valid_audit: AuditStamp,
    valid_name: CanonicalName,
    range_death_date: EventDateRange,
) -> None:
    """Verify ModelFormatError when living individual possesses death date or place."""
    with pytest.raises(ModelFormatError, match="death_date while is_deceased is False"):
        Individual(
            id=IndividualID(value="IND-000001"),
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_000001",
            death_date=range_death_date,
            is_deceased=False,
        )

    with pytest.raises(
        ModelFormatError, match="death_place_id while is_deceased is False"
    ):
        Individual(
            id=IndividualID(value="IND-000001"),
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_000001",
            death_place_id=SiteID(value="SID-000001"),
            is_deceased=False,
        )


@pytest.mark.regression
def test_individual_death_year_preceding_birth_year(
    valid_audit: AuditStamp, valid_name: CanonicalName
) -> None:
    """Verify ModelRangeError when death year precedes birth year."""
    b_date = EventDate(date=DateString(value="1920-05-10"))
    d_date = EventDate(date=DateString(value="1890-01-01"))

    with pytest.raises(ModelRangeError, match="Death year.*cannot precede birth year"):
        Individual(
            id=IndividualID(value="IND-000001"),
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_000001",
            birth_date=b_date,
            death_date=d_date,
        )


@pytest.mark.regression
def test_individual_duplicate_naming_lists(
    valid_audit: AuditStamp, valid_name: CanonicalName
) -> None:
    """Verify ModelFormatError on duplicate historical or alternate name entries."""
    alias = HistoricalName(raw_name="Jack Smith", status=NameStatus.COLLOQUIAL)

    with pytest.raises(
        ModelFormatError, match="Duplicate entries found in historical_names"
    ):
        Individual(
            id=IndividualID(value="IND-000001"),
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_000001",
            historical_names=[alias, alias],
        )

    with pytest.raises(
        ModelFormatError, match="Duplicate entries found in alternate_names"
    ):
        Individual(
            id=IndividualID(value="IND-000001"),
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_000001",
            alternate_names=["Johnny", "Johnny"],
        )
