"""Path: tests/test_gda/test_entity/test_facts/test_facts_util.py

Comprehensive test suite verifying Fact lifecycle, JSON I/O, and SQLite persistence.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gda.core.enums.archival import NoteType
from gda.core.enums.core import AssociatedRole, FactType
from gda.entity.facts.collection import Facts
from gda.entity.facts.errors import FactValidationError
from gda.entity.facts.util import (
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_fact,
    undelete_fact,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, FamilyID, NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.note import Note
from gda.model.base.source import SourceReference
from gda.model.base.tombstone import Tombstone
from gda.model.entity.fact import Fact, FactParticipant

__version__ = "1.0.0+build.3"


@pytest.mark.unit
def test_can_tombstone_and_tombstone_fact_guards(
    make_fact: Callable[..., Fact],
) -> None:
    """Verify can_tombstone and tombstone_fact enforce all integrity rules."""
    coll = Facts()
    now = IsoTimestamp("2026-11-15T12:00:00Z")

    ok, err = can_tombstone(coll, "FID-999999")
    assert ok is False
    assert "does not exist" in str(err)

    with pytest.raises(FactValidationError, match="does not exist"):
        tombstone_fact(coll, "FID-999999", reason="Missing")

    f1 = make_fact("FID-000001")
    f2 = make_fact("FID-000002")
    dead = make_fact(
        "FID-000003",
        tombstone=Tombstone[FactID]().retire(timestamp=now),
    )
    for f in (f1, f2, dead):
        coll.add(f)

    ok, err = can_tombstone(coll, dead.id)
    assert ok is False
    assert "already tombstoned" in str(err)

    ok, err = can_tombstone(coll, f1.id, superseded_by=f1.id)
    assert ok is False
    assert "cannot be the entity itself" in str(err)

    ok, err = can_tombstone(coll, f1.id, superseded_by="FID-888888")
    assert ok is False
    assert "does not exist" in str(err)

    ok, err = can_tombstone(coll, f1.id, superseded_by=dead.id)
    assert ok is False
    assert "itself tombstoned" in str(err)

    retired = tombstone_fact(coll, f1.id, reason="Merged", superseded_by=f2.id)
    assert retired.tombstone.is_deprecated is True
    assert retired.tombstone.superseded_by == f2.id
    assert retired.is_dirty is True


@pytest.mark.unit
def test_can_undelete_and_undelete_fact_guards(
    make_fact: Callable[..., Fact],
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
    mock_individuals_collection: MagicMock,
    mock_families_collection: MagicMock,
) -> None:
    """Verify can_undelete and undelete_fact check subject, participant, location, and site FKs."""
    coll = Facts()
    now = IsoTimestamp("2026-11-15T12:00:00Z")

    ok, err = can_undelete(coll, "FID-999999")
    assert ok is False
    assert "does not exist" in str(err)

    active = make_fact("FID-000001")
    coll.add(active)
    ok, err = can_undelete(coll, active.id)
    assert ok is False
    assert "is not tombstoned" in str(err)

    with pytest.raises(FactValidationError, match="is not tombstoned"):
        undelete_fact(coll, active.id)

    dead_bad_ind_subj = make_fact(
        "FID-000010",
        primary_subject_id="IND-999999",
        tombstone=Tombstone[FactID]().retire(timestamp=now),
    )
    coll.add(dead_bad_ind_subj)
    ok, err = can_undelete(
        coll,
        dead_bad_ind_subj.id,
        individuals_collection=mock_individuals_collection,
    )
    assert ok is False
    assert "primary subject individual 'IND-999999' is missing" in str(err)

    dead_bad_fam_subj = make_fact(
        "FID-000011",
        fact_type=FactType.MARRIAGE,
        primary_subject_id="FAM-999999",
        tombstone=Tombstone[FactID]().retire(timestamp=now),
    )
    coll.add(dead_bad_fam_subj)
    ok, err = can_undelete(
        coll,
        dead_bad_fam_subj.id,
        families_collection=mock_families_collection,
    )
    assert ok is False
    assert "primary subject family 'FAM-999999' is missing" in str(err)

    dead_bad_part = make_fact(
        "FID-000012",
        primary_subject_id="IND-000001",
        participants=[FactParticipant.create("IND-999999", AssociatedRole.WITNESS)],
        tombstone=Tombstone[FactID]().retire(timestamp=now),
    )
    coll.add(dead_bad_part)
    ok, err = can_undelete(
        coll,
        dead_bad_part.id,
        individuals_collection=mock_individuals_collection,
    )
    assert ok is False
    assert "participant individual 'IND-999999' is missing" in str(err)

    dead_bad_loc = make_fact(
        "FID-000002",
        location_id="LOC-999999",
        tombstone=Tombstone[FactID]().retire(timestamp=now),
    )
    coll.add(dead_bad_loc)
    ok, err = can_undelete(
        coll,
        dead_bad_loc.id,
        locations_collection=mock_locations_collection,
    )
    assert ok is False
    assert "governing location 'LOC-999999' is missing" in str(err)

    dead_bad_site = make_fact(
        "FID-000003",
        location_id="LOC-000001",
        site_id="SID-999999",
        tombstone=Tombstone[FactID]().retire(timestamp=now),
    )
    coll.add(dead_bad_site)
    ok, err = can_undelete(
        coll,
        dead_bad_site.id,
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )
    assert ok is False
    assert "venue site 'SID-999999' is missing" in str(err)

    valid_dead = make_fact(
        "FID-000004",
        location_id="LOC-000001",
        site_id="SID-000001",
        tombstone=Tombstone[FactID]().retire(timestamp=now),
    )
    coll.add(valid_dead)
    restored = undelete_fact(
        coll,
        valid_dead.id,
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
        individuals_collection=mock_individuals_collection,
        families_collection=mock_families_collection,
    )
    assert restored.tombstone.is_deprecated is False
    assert restored.is_dirty is True

    valid_fam_dead = make_fact(
        "FID-000006",
        fact_type=FactType.MARRIAGE,
        primary_subject_id="FAM-000001",
        location_id=None,
        site_id=None,
        participants=[],
        tombstone=Tombstone[FactID]().retire(timestamp=now),
    )
    coll.add(valid_fam_dead)
    restored_fam = undelete_fact(
        coll,
        valid_fam_dead.id,
        families_collection=mock_families_collection,
    )
    assert restored_fam.tombstone.is_deprecated is False

    standalone_dead = make_fact(
        "FID-000005",
        location_id=None,
        site_id=None,
        tombstone=Tombstone[FactID]().retire(timestamp=now),
    )
    coll.add(standalone_dead)
    restored_standalone = undelete_fact(coll, standalone_dead.id)
    assert restored_standalone.tombstone.is_deprecated is False


@pytest.mark.integration
def test_import_and_export_file_round_trip_and_branches(
    tmp_path: Path,
) -> None:
    """Verify import_file and export_file handle notes, participants, citations, audit, and graveyard flags."""
    assert import_file(Facts(), tmp_path / "nonexistent.json") == 0

    now = IsoTimestamp("2026-11-15T12:00:00Z")
    direct_note = Note.create(
        note_id=NoteID("NOT-000001"),
        note_type=NoteType.GENERAL,
        text="Direct note",
        audit=AuditStamp(created_at=now, updated_at=now),
    )
    direct_part = FactParticipant.create("IND-000020", AssociatedRole.CLERGY)
    direct_cit = SourceReference.create(
        citation_text="1880 Federal Census, p. 12",
        source_id="a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d",
    )

    payload = {
        "facts": [
            {
                "id": "FID-000001",
                "canonical_urn": "urn:gda:fact:birth_1",
                "fact_type": "BIRTH",
                "title": "Birth of John",
                "primary_subject_id": "IND-000001",
                "date": "1842-05-14",
                "location_id": "LOC-000001",
                "site_id": "SID-000001",
                "participants": [
                    {"individual_id": "IND-000010", "role": "WITNESS"},
                    direct_part,
                    "ignored-non-dict",
                ],
                "citations": [
                    {
                        "citation_text": "1850 Census",
                        "page_or_side": "14A",
                    },
                    direct_cit,
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
                "id": "FID-000002",
                "canonical_urn": "urn:gda:fact:marriage_1",
                "fact_type": FactType.MARRIAGE.value,
                "title": "Marriage",
                "primary_subject_id": FamilyID("FAM-000001"),
            },
        ]
    }
    in_path = tmp_path / "in_facts.json"
    in_path.write_text("{}", encoding="utf-8")

    coll = Facts()
    with patch("gda.io.json.GDAJsonIO.read", return_value=payload):
        assert import_file(coll, in_path) == 2

    f1 = coll["FID-000001"]
    assert len(f1.participants) == 2
    assert len(f1.citations) == 2
    assert len(f1.notes) == 3

    coll.soft_delete("FID-000002", reason="Duplicate", superseded_by="FID-000001")
    out_all = tmp_path / "export" / "all_facts.json"
    out_active = tmp_path / "export" / "active_facts.json"
    assert export_file(coll, out_all, include_graveyard=True) == 2
    assert export_file(coll, out_active, include_graveyard=False) == 1

    reimported = Facts()
    assert import_file(reimported, out_all) == 2
    assert len(reimported) == 1
    assert len(reimported.find_tombstoned()) == 1


@pytest.mark.unit
def test_load_from_db_and_save_to_db_with_mocked_mapper(
    active_fact: Fact,
) -> None:
    """Verify load_from_db and save_to_db execute queries via FactRowMapper."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{"id": "FID-000001"}]
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_cursor
    mock_tx = MagicMock()

    mock_session = MagicMock()
    mock_session.get_connection.return_value.__enter__.return_value = mock_conn
    mock_session.transaction.return_value.__enter__.return_value = mock_tx

    mock_mapper = MagicMock()
    mock_mapper.from_row.return_value = active_fact
    mock_mapper.to_row.return_value = {"id": "FID-000001", "title": "Birth"}

    with (
        patch("gda.db.session.DatabaseSessionManager", return_value=mock_session),
        patch("gda.db.schema.SchemaManager") as mock_schema_cls,
        patch(
            "gda.db.mapper.FactRowMapper",
            create=True,
            return_value=mock_mapper,
        ),
    ):
        coll = Facts([active_fact])
        assert save_to_db(coll) == 1
        assert mock_tx.execute.call_count == 1

        fresh = Facts()
        assert load_from_db(fresh) == 1
        assert len(fresh) == 1
        mock_schema_cls.return_value.init_db.assert_called()
