"""Path: tests/test_gda/test_entity/test_individuals/test_individuals_util.py

Comprehensive test suite verifying Individual lifecycle, JSON I/O, and SQLite persistence.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gda.core.enums.archival import NoteType
from gda.entity.individuals.collection import Individuals
from gda.entity.individuals.errors import IndividualValidationError
from gda.entity.individuals.util import (
    _check_place_ref,
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_individual,
    undelete_individual,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.individual import Individual

__version__ = "1.0.0+build.2"


@pytest.mark.unit
def test_can_tombstone_and_tombstone_individual_guards(
    make_individual: Callable[..., Individual],
) -> None:
    """Verify can_tombstone and tombstone_individual enforce all integrity rules."""
    coll = Individuals()
    now = IsoTimestamp("2026-11-15T12:00:00Z")

    ok, err = can_tombstone(coll, "IND-999999")
    assert ok is False
    assert "does not exist" in str(err)

    with pytest.raises(IndividualValidationError, match="does not exist"):
        tombstone_individual(coll, "IND-999999", reason="Missing")

    i1 = make_individual("IND-000001")
    i2 = make_individual("IND-000002")
    dead = make_individual(
        "IND-000003",
        tombstone=Tombstone[IndividualID]().retire(timestamp=now),
    )
    for ind in (i1, i2, dead):
        coll.add(ind)

    ok, err = can_tombstone(coll, dead.id)
    assert ok is False
    assert "already tombstoned" in str(err)

    ok, err = can_tombstone(coll, i1.id, superseded_by=i1.id)
    assert ok is False
    assert "cannot be the entity itself" in str(err)

    ok, err = can_tombstone(coll, i1.id, superseded_by="IND-888888")
    assert ok is False
    assert "does not exist" in str(err)

    ok, err = can_tombstone(coll, i1.id, superseded_by=dead.id)
    assert ok is False
    assert "itself tombstoned" in str(err)

    retired = tombstone_individual(coll, i1.id, reason="Merged", superseded_by=i2.id)
    assert retired.tombstone.is_deprecated is True
    assert retired.tombstone.superseded_by == i2.id
    assert retired.is_dirty is True


@pytest.mark.unit
def test_can_undelete_and_undelete_individual_guards(
    make_individual: Callable[..., Individual],
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
) -> None:
    """Verify can_undelete and undelete_individual check birth and death Location/Site FKs."""
    coll = Individuals()
    now = IsoTimestamp("2026-11-15T12:00:00Z")

    assert (
        _check_place_ref(
            "unexpected-type",  # type: ignore[arg-type]
            "birth place",
            IndividualID("IND-000001"),
            mock_locations_collection,
            mock_sites_collection,
        )
        is None
    )

    ok, err = can_undelete(coll, "IND-999999")
    assert ok is False
    assert "does not exist" in str(err)

    active = make_individual("IND-000001")
    coll.add(active)
    ok, err = can_undelete(coll, active.id)
    assert ok is False
    assert "is not tombstoned" in str(err)

    with pytest.raises(IndividualValidationError, match="is not tombstoned"):
        undelete_individual(coll, active.id)

    dead_bad_birth_loc = make_individual(
        "IND-000002",
        birth_place_id="LOC-999999",
        death_place_id=None,
        tombstone=Tombstone[IndividualID]().retire(timestamp=now),
    )
    coll.add(dead_bad_birth_loc)
    ok, err = can_undelete(
        coll,
        dead_bad_birth_loc.id,
        locations_collection=mock_locations_collection,
    )
    assert ok is False
    assert "birth place location 'LOC-999999' is missing" in str(err)

    dead_bad_death_site = make_individual(
        "IND-000003",
        birth_place_id="LOC-000001",
        death_place_id="SID-999999",
        tombstone=Tombstone[IndividualID]().retire(timestamp=now),
    )
    coll.add(dead_bad_death_site)
    ok, err = can_undelete(
        coll,
        dead_bad_death_site.id,
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )
    assert ok is False
    assert "death place site 'SID-999999' is missing" in str(err)

    valid_dead = make_individual(
        "IND-000004",
        birth_place_id="LOC-000001",
        death_place_id="SID-000001",
        tombstone=Tombstone[IndividualID]().retire(timestamp=now),
    )
    coll.add(valid_dead)
    restored = undelete_individual(
        coll,
        valid_dead.id,
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )
    assert restored.tombstone.is_deprecated is False
    assert restored.is_dirty is True

    standalone_dead = make_individual(
        "IND-000005",
        birth_place_id=None,
        death_place_id=None,
        tombstone=Tombstone[IndividualID]().retire(timestamp=now),
    )
    coll.add(standalone_dead)
    restored_standalone = undelete_individual(coll, standalone_dead.id)
    assert restored_standalone.tombstone.is_deprecated is False


@pytest.mark.integration
def test_import_and_export_file_round_trip_and_branches(
    tmp_path: Path,
) -> None:
    """Verify import_file and export_file handle NamePerson dicts/strings, mononyms, audit, and graveyard."""
    assert import_file(Individuals(), tmp_path / "nonexistent.json") == 0

    now = IsoTimestamp("2026-11-15T12:00:00Z")
    direct_note = Note.create(
        note_id=NoteID("NOT-000001"),
        note_type=NoteType.GENERAL,
        text="Direct note",
        audit=AuditStamp(created_at=now, updated_at=now),
    )

    payload = {
        "individuals": [
            {
                "id": "IND-000001",
                "name": {
                    "raw": "Abigail Smith",
                    "canonical": "Abigail Smith",
                    "given": "Abigail",
                    "surname": "Smith",
                    "aliases": ["Abby"],
                    "married": ["Adams"],
                },
                "canonical_urn": "urn:gda:ind:smith_abigail",
                "gender": "F",
                "birth_date": "1744-11-22",
                "death_date": "1818-10-28",
                "birth_place_id": "LOC-000001",
                "death_place_id": "SID-000001",
                "alternate_names": ["Abby", "First Lady Abby"],
                "married_names": ["Adams", "Quincy-Adams"],
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
                "id": "IND-000002",
                "name": "John Adams",
                "canonical_urn": "urn:gda:ind:adams_john",
                "sex": "M",
            },
            {
                "id": "IND-000003",
                "name": "Pocahontas",
                "canonical_urn": "urn:gda:ind:pocahontas",
                "sex": "F",
            },
        ]
    }
    in_path = tmp_path / "in_inds.json"
    in_path.write_text("{}", encoding="utf-8")

    coll = Individuals()
    with patch("gda.io.json.GDAJsonIO.read", return_value=payload):
        assert import_file(coll, in_path) == 3

    i1 = coll["IND-000001"]
    assert "First Lady Abby" in i1.aliases
    assert "Quincy-Adams" in i1.married_names
    assert len(i1.notes) == 3

    coll.soft_delete("IND-000002", reason="Duplicate", superseded_by="IND-000001")
    out_all = tmp_path / "export" / "all_inds.json"
    out_active = tmp_path / "export" / "active_inds.json"
    assert export_file(coll, out_all, include_graveyard=True) == 3
    assert export_file(coll, out_active, include_graveyard=False) == 2

    reimported = Individuals()
    assert import_file(reimported, out_all) == 3
    assert len(reimported) == 2
    assert len(reimported.find_tombstoned()) == 1


@pytest.mark.unit
def test_load_from_db_and_save_to_db_with_mocked_mapper(
    active_individual: Individual,
) -> None:
    """Verify load_from_db and save_to_db execute queries via IndividualRowMapper."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{"id": "IND-000001"}]
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_cursor
    mock_tx = MagicMock()

    mock_session = MagicMock()
    mock_session.get_connection.return_value.__enter__.return_value = mock_conn
    mock_session.transaction.return_value.__enter__.return_value = mock_tx

    mock_mapper = MagicMock()
    mock_mapper.from_row.return_value = active_individual
    mock_mapper.to_row.return_value = {"id": "IND-000001", "name": "John Quincy Adams"}

    with (
        patch("gda.db.session.DatabaseSessionManager", return_value=mock_session),
        patch("gda.db.schema.SchemaManager") as mock_schema_cls,
        patch(
            "gda.db.mapper.IndividualRowMapper",
            create=True,
            return_value=mock_mapper,
        ),
    ):
        coll = Individuals([active_individual])
        assert save_to_db(coll) == 1
        assert mock_tx.execute.call_count == 1

        fresh = Individuals()
        assert load_from_db(fresh) == 1
        assert len(fresh) == 1
        mock_schema_cls.return_value.init_db.assert_called()
