"""Path: tests/test_gda/test_entity/test_organizations/test_organizations_util.py

Comprehensive test suite verifying Organization lifecycle, JSON I/O, and SQLite persistence.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gda.core.enums.archival import NoteType
from gda.core.enums.orgs import OrganizationCategory
from gda.core.enums.vital import HistoricNameType
from gda.entity.organizations.collection import Organizations
from gda.entity.organizations.errors import (
    OrganizationHierarchyError,
    OrganizationValidationError,
)
from gda.entity.organizations.util import (
    _parse_event_date,
    _parse_time_period,
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_organization,
    undelete_organization,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import NoteID, OrganizationID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.organization import Organization

__version__ = "1.0.0+build.4"


# ==============================================================================
# GROUP 1: TOMBSTONE & CHILD REPARENTING LIFECYCLE
# ==============================================================================


@pytest.mark.unit
def test_can_tombstone_and_tombstone_organization_guards(
    make_organization: Callable[..., Organization],
) -> None:
    """Verify can_tombstone and tombstone_organization enforce all integrity and category rules."""
    coll = Organizations()
    now = IsoTimestamp("2026-11-15T12:00:00Z")

    ok, err = can_tombstone(coll, "ORG-999999")
    assert ok is False
    assert "does not exist" in str(err)

    with pytest.raises(OrganizationHierarchyError, match="does not exist"):
        tombstone_organization(coll, "ORG-999999", reason="Missing")

    parent1 = make_organization(
        "ORG-000001", name="State Lodge", category=OrganizationCategory.FRATERNAL
    )
    parent2 = make_organization(
        "ORG-000002", name="New State Lodge", category=OrganizationCategory.FRATERNAL
    )
    wrong_cat = make_organization(
        "ORG-000003", name="Civic Body", category=OrganizationCategory.CIVIC_SERVICE
    )
    dead_org = make_organization(
        "ORG-000004",
        name="Dead Lodge",
        category=OrganizationCategory.FRATERNAL,
        tombstone=Tombstone[OrganizationID]().retire(timestamp=now),
    )
    for o in (parent1, parent2, wrong_cat, dead_org):
        coll.add(o)

    ok, err = can_tombstone(coll, dead_org.id)
    assert ok is False
    assert "already tombstoned" in str(err)

    ok, err = can_tombstone(coll, parent1.id, superseded_by=parent1.id)
    assert ok is False
    assert "cannot be the entity itself" in str(err)

    ok, err = can_tombstone(coll, parent1.id, superseded_by="ORG-888888")
    assert ok is False
    assert "does not exist" in str(err)

    ok, err = can_tombstone(coll, parent1.id, superseded_by=dead_org.id)
    assert ok is False
    assert "itself tombstoned" in str(err)

    ok, err = can_tombstone(coll, parent1.id, superseded_by=wrong_cat.id)
    assert ok is False
    assert "must match the organization category" in str(err)

    # Add >3 active children to test overflow preview and atomic reparenting
    for idx in range(10, 14):
        coll.add(
            make_organization(
                f"ORG-0000{idx}",
                name=f"Chapter {idx}",
                category=OrganizationCategory.FRATERNAL,
                parent_org_id=str(parent1.id),
            )
        )

    ok, err = can_tombstone(coll, parent1.id)
    assert ok is False
    assert "total)" in str(err)

    # Also test <=3 active children preview branch
    small_coll = Organizations(
        [
            parent1,
            make_organization(
                "ORG-000020",
                name="Single Child",
                category=OrganizationCategory.FRATERNAL,
                parent_org_id=str(parent1.id),
            ),
        ]
    )
    ok_small, err_small = can_tombstone(small_coll, parent1.id)
    assert ok_small is False
    assert "total)" not in str(err_small)

    # Add a tombstoned child to parent1 so parent1's _parent_index bucket remains non-empty after active children reparent
    dead_child = make_organization(
        "ORG-000019",
        name="Retired Chapter",
        category=OrganizationCategory.FRATERNAL,
        parent_org_id=str(parent1.id),
        tombstone=Tombstone[OrganizationID]().retire(timestamp=now),
    )
    coll.add(dead_child)

    retired = tombstone_organization(
        coll,
        org_id=parent1.id,
        reason="Merged into New State Lodge",
        superseded_by=parent2.id,
    )
    assert retired.tombstone.is_deprecated is True
    assert retired.tombstone.superseded_by == parent2.id
    assert retired.is_dirty is True
    assert len(coll.find_children(parent2.id)) == 4
    assert parent1.id in coll._parent_index

    # Now retire parent2 into a 3rd fraternal parent when all children of parent2 are active (so _parent_index[parent2.id] is deleted)
    parent3 = make_organization(
        "ORG-000005", name="Supreme Lodge", category=OrganizationCategory.FRATERNAL
    )
    coll.add(parent3)
    tombstone_organization(
        coll,
        org_id=parent2.id,
        reason="Merged into Supreme Lodge",
        superseded_by=parent3.id,
    )
    assert parent2.id not in coll._parent_index


# ==============================================================================
# GROUP 2: UNDELETE LIFECYCLE OPERATORS
# ==============================================================================


@pytest.mark.unit
def test_can_undelete_and_undelete_organization_guards(
    make_organization: Callable[..., Organization],
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
) -> None:
    """Verify can_undelete and undelete_organization check parent, location, and site FKs."""
    coll = Organizations()
    now = IsoTimestamp("2026-11-15T12:00:00Z")

    ok, err = can_undelete(coll, "ORG-999999")
    assert ok is False
    assert "does not exist" in str(err)

    active = make_organization("ORG-000001")
    coll.add(active)
    ok, err = can_undelete(coll, active.id)
    assert ok is False
    assert "is not tombstoned" in str(err)

    with pytest.raises(OrganizationValidationError, match="is not tombstoned"):
        undelete_organization(coll, active.id)

    dead_with_missing_parent = make_organization(
        "ORG-000002",
        parent_org_id="ORG-000099",
        tombstone=Tombstone[OrganizationID]().retire(timestamp=now),
    )
    coll.add(dead_with_missing_parent)
    ok, err = can_undelete(coll, dead_with_missing_parent.id)
    assert ok is False
    assert "parent organization 'ORG-000099' is missing" in str(err)

    dead_with_bad_loc = make_organization(
        "ORG-000003",
        parent_org_id="ORG-000001",
        location_id="LOC-999999",
        tombstone=Tombstone[OrganizationID]().retire(timestamp=now),
    )
    coll.add(dead_with_bad_loc)
    ok, err = can_undelete(
        coll,
        dead_with_bad_loc.id,
        locations_collection=mock_locations_collection,
    )
    assert ok is False
    assert "governing location 'LOC-999999' is missing" in str(err)

    dead_with_bad_site = make_organization(
        "ORG-000004",
        parent_org_id="ORG-000001",
        location_id="LOC-000001",
        meeting_site_id="SID-999999",
        tombstone=Tombstone[OrganizationID]().retire(timestamp=now),
    )
    coll.add(dead_with_bad_site)
    ok, err = can_undelete(
        coll,
        dead_with_bad_site.id,
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )
    assert ok is False
    assert "meeting site 'SID-999999' is missing" in str(err)

    valid_dead = make_organization(
        "ORG-000005",
        parent_org_id="ORG-000001",
        location_id="LOC-000001",
        meeting_site_id="SID-000001",
        tombstone=Tombstone[OrganizationID]().retire(timestamp=now),
    )
    coll.add(valid_dead)
    restored = undelete_organization(
        coll,
        valid_dead.id,
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )
    assert restored.tombstone.is_deprecated is False
    assert restored.is_dirty is True

    standalone_dead = make_organization(
        "ORG-000006",
        parent_org_id=None,
        location_id=None,
        meeting_site_id=None,
        tombstone=Tombstone[OrganizationID]().retire(timestamp=now),
    )
    coll.add(standalone_dead)
    restored_standalone = undelete_organization(coll, standalone_dead.id)
    assert restored_standalone.tombstone.is_deprecated is False


# ==============================================================================
# GROUP 3: TEMPORAL PARSING, FILE I/O & DATABASE PERSISTENCE
# ==============================================================================


@pytest.mark.unit
def test_parse_event_date_and_time_period_branches() -> None:
    """Verify _parse_event_date and _parse_time_period handle all input variations."""
    ev = EventDate.create("1890")
    assert _parse_event_date(None) is None
    assert _parse_event_date(ev) is ev
    assert str(_parse_event_date({"date": "1900", "modifier": "EXACT"}).date) == "1900"
    assert str(_parse_event_date("1910").date) == "1910"

    tp = TimePeriod(start_date=ev)
    assert _parse_time_period(tp) is tp
    assert _parse_time_period(None) is None
    assert _parse_time_period("bad") is None
    assert _parse_time_period({}) is None
    parsed = _parse_time_period({"start_date": "1890", "end_date": "1950"})
    assert parsed is not None
    assert str(parsed.start_date.date) == "1890"


@pytest.mark.integration
def test_import_and_export_file_round_trip_and_branches(
    make_organization: Callable[..., Organization],
    tmp_path: Path,
) -> None:
    """Verify import_file and export_file handle all historical names, notes, audit, and graveyard flags."""
    assert import_file(Organizations(), tmp_path / "nonexistent.json") == 0

    now = IsoTimestamp("2026-11-15T12:00:00Z")
    direct_note = Note.create(
        note_id=NoteID("NOT-000001"),
        note_type=NoteType.GENERAL,
        text="Direct note",
        audit=AuditStamp(created_at=now, updated_at=now),
    )
    payload = {
        "organizations": [
            {
                "id": "ORG-000001",
                "name": {"raw": "Grand Lodge", "canonical": "Grand Lodge"},
                "category": "FRATERNAL",
                "canonical_urn": "urn:gda:org:nh:grand_lodge",
                "parent_org_id": None,
                "predecessor_ids": ["ORG-000010"],
                "successor_ids": ["ORG-000011"],
                "location_id": "LOC-000001",
                "meeting_site_id": "SID-000001",
                "period": {"start_date": "1850", "end_date": "1950"},
                "alternate_names": ["NH Grand Lodge", "NH Grand Lodge"],
                "historical_names": [
                    {
                        "raw": "Provincial Grand Lodge",
                        "canonical": "Provincial Grand Lodge",
                        "historic_name_type": HistoricNameType.HISTORICAL,
                    },
                    {
                        "raw_name": "Old Grand Lodge",
                        "canonical_name": "Old Grand Lodge",
                        "status": "COLONIAL",
                    },
                    "ignored-non-dict",
                ],
                "notes": [
                    {
                        "note_id": "NOT-000002",
                        "note_type": "RESEARCH",
                        "text": "With explicit audit",
                        "audit": {"created_at": str(now), "updated_at": str(now)},
                    },
                    {
                        "note_id": "NOT-000003",
                        "note_type": "GENERAL",
                        "text": "Without explicit audit",
                    },
                    direct_note,
                    "ignored-non-dict-note",
                ],
                "audit": {"created_at": str(now), "updated_at": str(now)},
                "tombstone": {
                    "is_deprecated": False,
                    "deprecated_at": None,
                    "superseded_by": None,
                },
            },
            {
                "id": "ORG-000002",
                "name": "Local Lodge No. 5",
                "category": "FRATERNAL",
                "canonical_urn": "urn:gda:org:nh:grand_lodge:lodge_5",
                "parent_org_id": "ORG-000001",
            },
        ]
    }
    in_path = tmp_path / "in_orgs.json"
    in_path.write_text("{}", encoding="utf-8")

    coll = Organizations()
    with patch("gda.io.json.GDAJsonIO.read", return_value=payload):
        assert import_file(coll, in_path) == 2

    org1 = coll["ORG-000001"]
    assert len(org1.historical_names) == 2
    assert len(org1.notes) == 3
    assert org1.predecessor_ids == [OrganizationID("ORG-000010")]
    assert org1.successor_ids == [OrganizationID("ORG-000011")]

    # Retire ORG-000002 with replacement ORG-000001 and test export/re-import round-trip
    coll.soft_delete("ORG-000002", reason="Dissolved", superseded_by="ORG-000001")
    out_all = tmp_path / "export" / "all_orgs.json"
    out_active = tmp_path / "export" / "active_orgs.json"
    assert export_file(coll, out_all, include_graveyard=True) == 2
    assert export_file(coll, out_active, include_graveyard=False) == 1

    reimported = Organizations()
    assert import_file(reimported, out_all) == 2
    assert len(reimported) == 1
    assert len(reimported.find_tombstoned()) == 1


@pytest.mark.unit
def test_load_from_db_and_save_to_db_with_mocked_mapper(
    active_organization: Organization,
) -> None:
    """Verify load_from_db and save_to_db execute queries via OrganizationRowMapper."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{"id": "ORG-000001"}]
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_cursor
    mock_tx = MagicMock()

    mock_session = MagicMock()
    mock_session.get_connection.return_value.__enter__.return_value = mock_conn
    mock_session.transaction.return_value.__enter__.return_value = mock_tx

    mock_mapper = MagicMock()
    mock_mapper.from_row.return_value = active_organization
    mock_mapper.to_row.return_value = {"id": "ORG-000001", "name": "VFW Post 411"}

    with (
        patch("gda.db.session.DatabaseSessionManager", return_value=mock_session),
        patch("gda.db.schema.SchemaManager") as mock_schema_cls,
        patch(
            "gda.db.mapper.OrganizationRowMapper",
            create=True,
            return_value=mock_mapper,
        ),
    ):
        coll = Organizations([active_organization])
        assert save_to_db(coll) == 1
        assert mock_tx.execute.call_count == 1

        fresh = Organizations()
        assert load_from_db(fresh) == 1
        assert len(fresh) == 1
        mock_schema_cls.return_value.init_db.assert_called()
