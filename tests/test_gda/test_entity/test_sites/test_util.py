"""Path: tests/test_gda/test_entity/test_sites/test_util.py

Comprehensive test suite verifying Site lifecycle, JSON I/O, and SQLite persistence.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gda.entity.sites.collection import Sites
from gda.entity.sites.errors import SiteValidationError
from gda.entity.sites.util import (
    _parse_event_date,
    _parse_time_period,
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_site,
    undelete_site,
)
from gda.enums.archival import NoteType
from gda.model.atom.date import EventDate, IsoTimestamp
from gda.model.atom.geo import Coordinates, Latitude, Longitude
from gda.model.atom.id import NoteID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.note import Note
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import Tombstone
from gda.model.entity.site import Site

__version__ = "1.0.0+build.11"


# ==============================================================================
# GROUP 1: TOMBSTONE LIFECYCLE OPERATORS
# Note: Verifies can_tombstone and tombstone_site validation guards and retirement
# ==============================================================================


@pytest.mark.regression
def test_can_tombstone_active_site_returns_true(make_site) -> None:
    """Verify active site can be tombstoned."""
    site = make_site("SID-000001")
    coll = MagicMock()
    coll._registry = {site.id: site}

    ok, err = can_tombstone(coll, "SID-000001")
    assert ok is True
    assert err is None


@pytest.mark.regression
def test_can_tombstone_nonexistent_site_returns_false() -> None:
    """Verify nonexistent site returns error message."""
    coll = MagicMock()
    coll._registry = {}

    ok, err = can_tombstone(coll, "SID-000099")
    assert ok is False
    assert "does not exist in collection" in err


@pytest.mark.regression
def test_can_tombstone_already_tombstoned_returns_false(tombstoned_site) -> None:
    """Verify already deprecated site returns error message."""
    coll = MagicMock()
    coll._registry = {tombstoned_site.id: tombstoned_site}

    ok, err = can_tombstone(coll, tombstoned_site.id)
    assert ok is False
    assert "is already tombstoned" in err


@pytest.mark.regression
def test_can_tombstone_self_supersession_returns_false(make_site) -> None:
    """Verify self-supersession returns error message."""
    site = make_site("SID-000001")
    coll = MagicMock()
    coll._registry = {site.id: site}

    ok, err = can_tombstone(coll, "SID-000001", superseded_by="SID-000001")
    assert ok is False
    assert "cannot be the entity itself" in err


@pytest.mark.regression
def test_can_tombstone_missing_replacement_returns_false(make_site) -> None:
    """Verify missing replacement returns error message."""
    site = make_site("SID-000001")
    coll = MagicMock()
    coll._registry = {site.id: site}

    ok, err = can_tombstone(coll, "SID-000001", superseded_by="SID-000002")
    assert ok is False
    assert "does not exist in collection" in err


@pytest.mark.regression
def test_can_tombstone_tombstoned_replacement_returns_false(make_site) -> None:
    """Verify superseded_by pointing to tombstoned replacement returns error message."""
    now = IsoTimestamp.now_utc()
    site1 = make_site("SID-000001")
    site2 = make_site("SID-000002", tombstone=Tombstone[SiteID]().retire(timestamp=now))
    coll = MagicMock()
    coll._registry = {site1.id: site1, site2.id: site2}

    ok, err = can_tombstone(coll, "SID-000001", superseded_by="SID-000002")
    assert ok is False
    assert "is itself tombstoned" in err


@pytest.mark.regression
def test_tombstone_site_success_stamps_entity_and_updates_registry(make_site) -> None:
    """Verify tombstone_site updates entity with retirement details."""
    site1 = make_site("SID-000001")
    site2 = make_site("SID-000002")
    coll = MagicMock()
    coll._registry = {site1.id: site1, site2.id: site2}

    retired = tombstone_site(
        collection=coll,
        site_id="SID-000001",
        reason="Facility merged",
        superseded_by="SID-000002",
    )

    assert retired.tombstone.is_deprecated is True
    assert retired.tombstone.superseded_by == SiteID("SID-000002")
    assert coll._registry[site1.id] is retired


@pytest.mark.regression
def test_tombstone_site_failure_raises_site_validation_error() -> None:
    """Verify invalid tombstone request raises SiteValidationError."""
    coll = MagicMock()
    coll._registry = {}

    with pytest.raises(SiteValidationError, match="does not exist in collection"):
        tombstone_site(collection=coll, site_id="SID-000099", reason="Test")


# ==============================================================================
# GROUP 2: UNDELETE LIFECYCLE OPERATORS
# Note: Verifies can_undelete and undelete_site reactivation logic and FK guards
# ==============================================================================


@pytest.mark.regression
def test_can_undelete_tombstoned_site_returns_true(
    tombstoned_site, mock_locations_collection
) -> None:
    """Verify valid tombstoned site can be restored."""
    coll = MagicMock()
    coll._registry = {tombstoned_site.id: tombstoned_site}

    ok, err = can_undelete(coll, tombstoned_site.id, locations_collection=mock_locations_collection)
    assert ok is True
    assert err is None


@pytest.mark.regression
def test_can_undelete_nonexistent_site_returns_false() -> None:
    """Verify nonexistent site cannot be undeleted."""
    coll = MagicMock()
    coll._registry = {}

    ok, err = can_undelete(coll, "SID-000099")
    assert ok is False
    assert "does not exist in collection" in err


@pytest.mark.regression
def test_can_undelete_active_site_returns_false(active_site) -> None:
    """Verify active site cannot be undeleted."""
    coll = MagicMock()
    coll._registry = {active_site.id: active_site}

    ok, err = can_undelete(coll, active_site.id)
    assert ok is False
    assert "is not tombstoned" in err


@pytest.mark.regression
def test_can_undelete_missing_governing_location_returns_false(make_site) -> None:
    """Verify undeleting site with missing governing location returns false."""
    now = IsoTimestamp.now_utc()
    site = make_site(
        "SID-000001",
        location_id="LOC-000099",
        tombstone=Tombstone[SiteID]().retire(timestamp=now),
    )
    coll = MagicMock()
    coll._registry = {site.id: site}

    loc_coll = MagicMock()
    loc_coll.__contains__.return_value = False

    ok, err = can_undelete(coll, "SID-000001", locations_collection=loc_coll)
    assert ok is False
    assert "governing location 'LOC-000099' is missing or tombstoned" in err


@pytest.mark.regression
def test_undelete_site_success_reactivates_entity_and_marks_dirty(tombstoned_site) -> None:
    """Verify undelete_site clears tombstone and marks site dirty."""
    coll = MagicMock()
    coll._registry = {tombstoned_site.id: tombstoned_site}

    restored = undelete_site(coll, tombstoned_site.id)

    assert restored.tombstone.is_deprecated is False
    assert restored.tombstone.superseded_by is None
    assert restored.is_dirty is True
    assert coll._registry[tombstoned_site.id] is restored


@pytest.mark.regression
def test_undelete_site_failure_raises_site_validation_error(active_site) -> None:
    """Verify invalid undelete request raises SiteValidationError."""
    coll = MagicMock()
    coll._registry = {active_site.id: active_site}

    with pytest.raises(SiteValidationError, match="is not tombstoned"):
        undelete_site(coll, active_site.id)


# ==============================================================================
# GROUP 3: DATABASE PERSISTENCE ROUND-TRIPS
# Note: Verifies load_from_db and save_to_db execution via SiteRowMapper
# ==============================================================================


@pytest.mark.regression
@patch("gda.db.session.DatabaseSessionManager")
@patch("gda.db.schema.SchemaManager")
@patch("gda.db.mapper.SiteRowMapper")
def test_load_from_db_populates_collection(
    mock_mapper_cls: MagicMock,
    mock_schema_cls: MagicMock,
    mock_session_cls: MagicMock,
    make_site,
) -> None:
    """Verify load_from_db reads records and adds to collection."""
    mock_session = MagicMock()
    mock_session_cls.return_value = mock_session
    mock_conn = MagicMock()
    mock_session.get_connection.return_value.__enter__.return_value = mock_conn

    raw_row = {"id": "SID-000001"}
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [raw_row]
    mock_conn.execute.return_value = mock_cursor

    mock_mapper = MagicMock()
    mock_mapper_cls.return_value = mock_mapper
    mock_site = make_site("SID-000001")
    mock_mapper.from_row.return_value = mock_site

    coll = MagicMock()
    count = load_from_db(coll)

    assert count == 1
    coll.add.assert_called_once_with(mock_site)
    coll.mark_clean.assert_called_once()


@pytest.mark.regression
@patch("gda.db.session.DatabaseSessionManager")
@patch("gda.db.schema.SchemaManager")
@patch("gda.db.mapper.SiteRowMapper")
def test_save_to_db_persists_entities(
    mock_mapper_cls: MagicMock,
    mock_schema_cls: MagicMock,
    mock_session_cls: MagicMock,
    make_site,
) -> None:
    """Verify save_to_db persists all entities inside a transaction."""
    mock_session = MagicMock()
    mock_session_cls.return_value = mock_session
    mock_tx = MagicMock()
    mock_session.transaction.return_value.__enter__.return_value = mock_tx

    site = make_site("SID-000001")
    coll = MagicMock()
    coll.iter_all.return_value = [site]

    mock_mapper = MagicMock()
    mock_mapper_cls.return_value = mock_mapper
    mock_mapper.to_row.return_value = {"id": "SID-000001", "name": "Old First Church"}

    count = save_to_db(coll)

    assert count == 1
    assert mock_tx.execute.call_count == 1
    coll.mark_clean.assert_called_once()


# ==============================================================================
# GROUP 4: TIMEPERIOD PARSER & JSON IMPORT/EXPORT SERIALIZATION
# ==============================================================================


@pytest.mark.regression
def test_parse_event_date_variations() -> None:
    """Verify _parse_event_date handles None, EventDate, dict, and string scalar inputs."""
    d = EventDate.create("1800")
    assert _parse_event_date(None) is None
    assert _parse_event_date(d) is d
    assert _parse_event_date({"date": "1820", "modifier": "EXACT"}).year == 1820
    assert _parse_event_date("1850").year == 1850


@pytest.mark.regression
def test_parse_time_period_direct_object_and_edge_cases() -> None:
    """Verify _parse_time_period supports direct objects, strings, dicts, and empty inputs."""
    d_start = EventDate.create("1800")
    period = TimePeriod(start_date=d_start)

    assert _parse_time_period(period) is period
    assert _parse_time_period(None) is None
    assert _parse_time_period("invalid") is None
    assert _parse_time_period({}) is None

    parsed_dates = _parse_time_period(
        {
            "start_date": {"date": "1800", "modifier": "EXACT"},
            "end_date": {"date": "1900", "modifier": "EXACT"},
        }
    )
    assert parsed_dates is not None
    assert parsed_dates.start_date.year == 1800
    assert parsed_dates.end_date.year == 1900

    parsed_strings = _parse_time_period({"start_date": "1840", "end_date": "1910"})
    assert parsed_strings is not None
    assert parsed_strings.start_date.year == 1840
    assert parsed_strings.end_date.year == 1910


@pytest.mark.regression
@patch("gda.io.json.GDAJsonIO.read")
@patch("pathlib.Path.exists")
def test_import_file_reads_and_adds_sites(
    mock_exists: MagicMock,
    mock_read: MagicMock,
) -> None:
    """Verify import_file deserializes JSON and populates collection."""
    mock_exists.return_value = True
    now = IsoTimestamp.now_utc()
    existing_note = Note.create(
        note_id=NoteID("NOT-000002"),
        note_type=NoteType.RESEARCH,
        text="Existing Note Instance",
        audit=AuditStamp(created_at=now, updated_at=now),
    )
    now_str = "2026-11-03T00:00:00Z"
    payload = {
        "sites": [
            {
                "id": "SID-000001",
                "name": {"raw": "Old First Church", "canonical": "Old First Church"},
                "category": "CHURCH",
                "canonical_urn": "urn:gda:site:us:nh:bow:church_s000001",
                "location_id": "LOC-000001",
                "historical_names": [
                    {
                        "raw": "Historic First Church",
                        "canonical": "Historic First Church",
                        "status": "HISTORICAL",
                    }
                ],
                "alternate_names": ["The Meetinghouse"],
                "notes": [
                    {
                        "note_id": "NOT-000001",
                        "note_type": "GENERAL",
                        "text": "Foundation laid 1800",
                        "audit": {"created_at": now_str, "updated_at": now_str},
                    },
                    existing_note,
                ],
                "address": {
                    "address_line_1": "10 Main St",
                    "city": "Bow",
                    "state": "NH",
                    "postal_code": "03304",
                },
                "period": {"start_date": "1800", "end_date": "1900"},
                "is_active": True,
            },
            {
                "id": "SID-000002",
                "name": "Second Parish Church",
                "category": "CHURCH",
                "canonical_urn": "urn:gda:site:us:nh:bow:second_church_s000002",
                "location_id": "LOC-000001",
                "period": TimePeriod(start_date=EventDate.create("1850")),
            },
        ]
    }
    mock_read.return_value = payload

    coll = MagicMock()
    count = import_file(coll, "dummy.json")

    assert count == 2
    assert coll.add.call_count == 2
    added_site = coll.add.call_args_list[0][0][0]
    assert isinstance(added_site, Site)
    assert added_site.id == SiteID("SID-000001")
    assert added_site.name.canonical == "Old First Church"
    assert "The Meetinghouse" in added_site.aliases
    assert added_site.period is not None


@pytest.mark.regression
@patch("gda.io.json.GDAJsonIO.read")
@patch("pathlib.Path.exists")
def test_import_file_ignores_non_dict_historical_names(
    mock_exists: MagicMock,
    mock_read: MagicMock,
) -> None:
    """Verify import_file skips non-dict entries in historical_names (branch 347->346)."""
    mock_exists.return_value = True
    payload = {
        "sites": [
            {
                "id": "SID-000001",
                "name": "First Parish Church",
                "category": "CHURCH",
                "canonical_urn": "urn:gda:site:loc_001:church_s000001",
                "location_id": "LOC-000001",
                "historical_names": [
                    "invalid-non-dict-entry",
                    {
                        "raw": "Historic First Church",
                        "canonical": "Historic First Church",
                        "status": "HISTORICAL",
                    },
                ],
            }
        ]
    }
    mock_read.return_value = payload

    coll = MagicMock()
    count = import_file(coll, "dummy.json")

    assert count == 1
    added_site = coll.add.call_args[0][0]
    assert len(added_site.historical_names) == 1
    assert added_site.historical_names[0].name == "Historic First Church"


@pytest.mark.regression
@patch("pathlib.Path.exists")
def test_import_file_nonexistent_returns_zero(mock_exists: MagicMock) -> None:
    """Verify import_file returns 0 when file does not exist."""
    mock_exists.return_value = False
    coll = MagicMock()
    assert import_file(coll, "missing.json") == 0


@pytest.mark.regression
@patch("gda.io.json.GDAJsonIO.write")
@patch("pathlib.Path.mkdir")
def test_export_file_writes_payload(
    mock_mkdir: MagicMock,
    mock_write: MagicMock,
    make_site,
) -> None:
    """Verify export_file formats collection entities into JSON payload."""
    now = IsoTimestamp.now_utc()
    site = make_site("SID-000001")
    site = site.add_alias("Old Chapel")
    site = site.add_historic_variant("Old Log Meetinghouse")
    note = Note.create(
        note_id=NoteID("NOT-000001"),
        note_type=NoteType.RESEARCH,
        text="Sample note",
        audit=AuditStamp(created_at=now, updated_at=now),
    )
    site = site.update_note(note.note_id, text="Updated text")
    object.__setattr__(site, "notes", [note])

    coll = MagicMock()
    coll.iter_all.return_value = [site]

    count = export_file(coll, "dummy_out.json", include_graveyard=True)

    assert count == 1
    assert mock_write.call_count == 1
    payload = mock_write.call_args[0][1]
    assert payload["total_count"] == 1
    assert payload["sites"][0]["id"] == "SID-000001"
    assert "Old Chapel" in payload["sites"][0]["alternate_names"]
    assert payload["sites"][0]["coordinates"] is None


@pytest.mark.regression
@patch("gda.io.json.GDAJsonIO.write")
@patch("pathlib.Path.mkdir")
def test_export_file_writes_payload_with_coordinates(
    mock_mkdir: MagicMock,
    mock_write: MagicMock,
    make_site,
) -> None:
    """Verify export_file formats coordinates when populated."""
    coords = Coordinates(latitude=Latitude(43.12345), longitude=Longitude(-71.54321))
    site = make_site("SID-000001")
    object.__setattr__(site, "coordinates", coords)

    coll = MagicMock()
    coll.iter_all.return_value = [site]

    count = export_file(coll, "dummy_out.json", include_graveyard=True)

    assert count == 1
    assert mock_write.call_count == 1
    payload = mock_write.call_args[0][1]
    assert payload["sites"][0]["coordinates"] == {"latitude": 43.12345, "longitude": -71.54321}


@pytest.mark.regression
@patch("gda.io.json.GDAJsonIO.write")
@patch("pathlib.Path.mkdir")
def test_export_file_without_graveyard_filters_tombstoned(
    mock_mkdir: MagicMock,
    mock_write: MagicMock,
    make_site,
) -> None:
    """Verify export_file honors include_graveyard=False branch."""
    now = IsoTimestamp.now_utc()
    active = make_site("SID-000001")
    tomb = Tombstone[SiteID]().retire(timestamp=now)
    dead = make_site("SID-000002", tombstone=tomb)

    coll = Sites([active, dead])
    count = export_file(coll, "dummy_out.json", include_graveyard=False)

    assert count == 1
    payload = mock_write.call_args[0][1]
    assert payload["total_count"] == 1
    assert payload["sites"][0]["id"] == "SID-000001"
