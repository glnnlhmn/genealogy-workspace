"""Path: tests/test_gda/test_entity/test_families/test_families_util.py

Comprehensive test suite verifying Family lifecycle, JSON I/O, and SQLite persistence.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gda.core.enums.archival import NoteType
from gda.core.enums.vital import PedigreeType
from gda.entity.families.collection import Families
from gda.entity.families.errors import FamilyValidationError
from gda.entity.families.util import (
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_family,
    undelete_family,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FamilyID, NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.family import ChildLink
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.family import Family

__version__ = "1.0.0+build.2"


@pytest.mark.unit
def test_can_tombstone_and_tombstone_family_guards(
    make_family: Callable[..., Family],
) -> None:
    """Verify can_tombstone and tombstone_family enforce all integrity rules."""
    coll = Families()
    now = IsoTimestamp("2026-11-15T12:00:00Z")

    ok, err = can_tombstone(coll, "FAM-999999")
    assert ok is False
    assert "does not exist" in str(err)

    with pytest.raises(FamilyValidationError, match="does not exist"):
        tombstone_family(coll, "FAM-999999", reason="Missing")

    f1 = make_family("FAM-000001")
    f2 = make_family("FAM-000002")
    dead = make_family(
        "FAM-000003",
        tombstone=Tombstone[FamilyID]().retire(timestamp=now),
    )
    for fam in (f1, f2, dead):
        coll.add(fam)

    ok, err = can_tombstone(coll, dead.id)
    assert ok is False
    assert "already tombstoned" in str(err)

    ok, err = can_tombstone(coll, f1.id, superseded_by=f1.id)
    assert ok is False
    assert "cannot be the entity itself" in str(err)

    ok, err = can_tombstone(coll, f1.id, superseded_by="FAM-888888")
    assert ok is False
    assert "does not exist" in str(err)

    ok, err = can_tombstone(coll, f1.id, superseded_by=dead.id)
    assert ok is False
    assert "itself tombstoned" in str(err)

    retired = tombstone_family(coll, f1.id, reason="Merged", superseded_by=f2.id)
    assert retired.tombstone.is_deprecated is True
    assert retired.tombstone.superseded_by == f2.id
    assert retired.is_dirty is True


@pytest.mark.unit
def test_can_undelete_and_undelete_family_guards(
    make_family: Callable[..., Family],
    mock_individuals_collection: MagicMock,
) -> None:
    """Verify can_undelete and undelete_family check partner and child Individual FKs."""
    coll = Families()
    now = IsoTimestamp("2026-11-15T12:00:00Z")

    ok, err = can_undelete(coll, "FAM-999999")
    assert ok is False
    assert "does not exist" in str(err)

    active = make_family("FAM-000001")
    coll.add(active)
    ok, err = can_undelete(coll, active.id)
    assert ok is False
    assert "is not tombstoned" in str(err)

    with pytest.raises(FamilyValidationError, match="is not tombstoned"):
        undelete_family(coll, active.id)

    dead_bad_partner = make_family(
        "FAM-000002",
        partner_ids=["IND-999999"],
        children=[],
        tombstone=Tombstone[FamilyID]().retire(timestamp=now),
    )
    coll.add(dead_bad_partner)
    ok, err = can_undelete(
        coll,
        dead_bad_partner.id,
        individuals_collection=mock_individuals_collection,
    )
    assert ok is False
    assert "partner individual 'IND-999999' is missing" in str(err)

    dead_bad_child = make_family(
        "FAM-000003",
        partner_ids=["IND-000001"],
        children=[("IND-999999", PedigreeType.BIRTH)],
        tombstone=Tombstone[FamilyID]().retire(timestamp=now),
    )
    coll.add(dead_bad_child)
    ok, err = can_undelete(
        coll,
        dead_bad_child.id,
        individuals_collection=mock_individuals_collection,
    )
    assert ok is False
    assert "child individual 'IND-999999' is missing" in str(err)

    valid_dead = make_family(
        "FAM-000004",
        partner_ids=["IND-000001", "IND-000002"],
        children=[("IND-000003", PedigreeType.BIRTH)],
        tombstone=Tombstone[FamilyID]().retire(timestamp=now),
    )
    coll.add(valid_dead)
    restored = undelete_family(
        coll,
        valid_dead.id,
        individuals_collection=mock_individuals_collection,
    )
    assert restored.tombstone.is_deprecated is False
    assert restored.is_dirty is True

    standalone_dead = make_family(
        "FAM-000005",
        tombstone=Tombstone[FamilyID]().retire(timestamp=now),
    )
    coll.add(standalone_dead)
    restored_standalone = undelete_family(coll, standalone_dead.id)
    assert restored_standalone.tombstone.is_deprecated is False


@pytest.mark.integration
def test_import_and_export_file_round_trip_and_branches(
    tmp_path: Path,
) -> None:
    """Verify import_file and export_file handle partners, children, union, notes, audit, and graveyard."""
    assert import_file(Families(), tmp_path / "nonexistent.json") == 0

    now = IsoTimestamp("2026-11-15T12:00:00Z")
    direct_note = Note.create(
        note_id=NoteID("NOT-000001"),
        note_type=NoteType.GENERAL,
        text="Direct note",
        audit=AuditStamp(created_at=now, updated_at=now),
    )
    direct_child = ChildLink.create("IND-000004", PedigreeType.ADOPTED)

    payload = {
        "families": [
            {
                "id": "FAM-000001",
                "canonical_urn": "urn:gda:fam:adams_1",
                "partner_ids": ["IND-000001", "IND-000002"],
                "children": [
                    {"child_id": "IND-000003", "pedigree": "BIRTH"},
                    direct_child,
                    ("IND-000005", "FOSTER"),
                    "ignored-non-child-link",
                ],
                "union": {"union_type": "MARRIAGE"},
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
                "id": "FAM-000002",
                "canonical_urn": "urn:gda:fam:adams_2",
            },
        ]
    }
    in_path = tmp_path / "in_fams.json"
    in_path.write_text("{}", encoding="utf-8")

    coll = Families()
    with patch("gda.io.json.GDAJsonIO.read", return_value=payload):
        assert import_file(coll, in_path) == 2

    f1 = coll["FAM-000001"]
    assert len(f1.children) == 3
    assert len(f1.notes) == 3

    coll.soft_delete("FAM-000002", reason="Duplicate", superseded_by="FAM-000001")
    out_all = tmp_path / "export" / "all_fams.json"
    out_active = tmp_path / "export" / "active_fams.json"
    assert export_file(coll, out_all, include_graveyard=True) == 2
    assert export_file(coll, out_active, include_graveyard=False) == 1

    reimported = Families()
    assert import_file(reimported, out_all) == 2
    assert len(reimported) == 1
    assert len(reimported.find_tombstoned()) == 1


@pytest.mark.unit
def test_load_from_db_and_save_to_db_with_mocked_mapper(
    active_family: Family,
) -> None:
    """Verify load_from_db and save_to_db execute queries via FamilyRowMapper."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{"id": "FAM-000001"}]
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_cursor
    mock_tx = MagicMock()

    mock_session = MagicMock()
    mock_session.get_connection.return_value.__enter__.return_value = mock_conn
    mock_session.transaction.return_value.__enter__.return_value = mock_tx

    mock_mapper = MagicMock()
    mock_mapper.from_row.return_value = active_family
    mock_mapper.to_row.return_value = {"id": "FAM-000001", "canonical_urn": "urn:gda:fam:unit"}

    with (
        patch("gda.db.session.DatabaseSessionManager", return_value=mock_session),
        patch("gda.db.schema.SchemaManager") as mock_schema_cls,
        patch(
            "gda.db.mapper.FamilyRowMapper",
            create=True,
            return_value=mock_mapper,
        ),
    ):
        coll = Families([active_family])
        assert save_to_db(coll) == 1
        assert mock_tx.execute.call_count == 1

        fresh = Families()
        assert load_from_db(fresh) == 1
        assert len(fresh) == 1
        mock_schema_cls.return_value.init_db.assert_called()
