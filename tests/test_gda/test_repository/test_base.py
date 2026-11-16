"""Path: tests/test_gda/test_repository/test_base.py

Unit tests for BaseSQLiteRepository CRUD, query execution, and error translation.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from gda.db.exceptions import EntityMappingError
from gda.db.mapper.base import BaseRowMapper
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import SiteID
from gda.repository.base import BaseSQLiteRepository
from gda.repository.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
    RepositoryError,
)
from gda.repository.query import SortOrder


@dataclass(frozen=True)
class DummySourceRecord:
    """Lightweight domain record for testing BaseSQLiteRepository."""

    id: SiteID
    canonical_urn: str
    title: str
    year: int


class DummyRecordMapper(BaseRowMapper[DummySourceRecord]):
    """Row mapper for DummySourceRecord."""

    def __init__(self) -> None:
        """Initialize DummyRecordMapper."""
        super().__init__(DummySourceRecord)

    def to_row(self, entity: DummySourceRecord) -> dict[str, Any]:
        """Serialize DummySourceRecord to SQLite row dict."""
        if entity.title.startswith("FAIL_TO_ROW"):
            raise EntityMappingError("Simulated serialization failure")
        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            "title": entity.title,
            "year": entity.year,
        }

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> DummySourceRecord:
        """Hydrate DummySourceRecord from SQLite row."""
        data = dict(row)
        if str(data.get("title", "")).startswith("FAIL_FROM_ROW"):
            raise EntityMappingError("Simulated hydration failure")
        return DummySourceRecord(
            id=SiteID(data["id"]),
            canonical_urn=str(data["canonical_urn"]),
            title=str(data["title"]),
            year=int(data["year"]),
        )


class DummyRecordRepository(BaseSQLiteRepository[DummySourceRecord, SiteID]):
    """Concrete repository implementation for DummySourceRecord."""

    @property
    def table_name(self) -> str:
        """Return test table name."""
        return "dummy_records"


@pytest.fixture
def repo(tmp_path: Path) -> DummyRecordRepository:
    """Provision an initialized SQLite database and DummyRecordRepository."""
    db_file = tmp_path / "test_repo.db"
    session = DatabaseSessionManager(db_path=db_file)
    with session.transaction() as conn:
        conn.execute(
            """
            CREATE TABLE dummy_records (
                id TEXT PRIMARY KEY,
                canonical_urn TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                year INTEGER NOT NULL
            );
            """
        )
    return DummyRecordRepository(mapper=DummyRecordMapper(), session_manager=session)


def _make_record(idx: int, title: str = "Record", year: int = 1900) -> DummySourceRecord:
    """Create a DummySourceRecord test fixture."""
    return DummySourceRecord(
        id=SiteID(f"SID-{idx:06d}"),
        canonical_urn=f"urn:gda:dummy:{idx:03d}",
        title=f"{title} {idx}",
        year=year,
    )


def test_repository_properties_and_default_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify repository properties and default DatabaseSessionManager instantiation."""
    default_db = tmp_path / "default.db"
    monkeypatch.setenv("GDA_DB_PATH", str(default_db))
    mapper = DummyRecordMapper()
    default_repo = DummyRecordRepository(mapper=mapper)
    assert default_repo.table_name == "dummy_records"
    assert default_repo.primary_key == "id"
    assert default_repo.mapper is mapper
    assert isinstance(default_repo.session_manager, DatabaseSessionManager)


def test_insert_get_get_or_raise_and_duplicate_detection(
    repo: DummyRecordRepository,
) -> None:
    """Verify insert, get, get_or_raise, get_by_urn, exists, and DuplicateRecordError."""
    rec = _make_record(1, title="Parish Register", year=1885)
    assert repo.exists(rec.id) is False
    assert repo.get(rec.id) is None

    with pytest.raises(RecordNotFoundError) as exc_info:
        repo.get_or_raise(rec.id)
    assert exc_info.value.table_name == "dummy_records"

    persisted = repo.insert(rec)
    assert persisted == rec
    assert repo.exists(rec.id) is True
    assert repo.exists(rec.id.value) is True

    loaded = repo.get(rec.id)
    assert loaded == rec
    assert repo.get_or_raise(rec.id.value) == rec
    assert repo.get_by_urn(rec.canonical_urn) == rec
    assert repo.get_by_urn("urn:gda:dummy:missing") is None

    with pytest.raises(DuplicateRecordError):
        repo.insert(rec)


def test_upsert_and_upsert_many_and_delete(repo: DummyRecordRepository) -> None:
    """Verify upsert, upsert_many (including empty batch), and delete operations."""
    assert repo.upsert_many([]) == 0

    r1 = _make_record(1, title="Original", year=1870)
    r2 = _make_record(2, title="Second", year=1880)
    r3 = _make_record(3, title="Third", year=1890)

    count = repo.upsert_many([r1, r2, r3])
    assert count == 3
    assert repo.count() == 3

    r1_updated = DummySourceRecord(
        id=r1.id,
        canonical_urn=r1.canonical_urn,
        title="Updated Title",
        year=1875,
    )
    repo.upsert(r1_updated)
    assert repo.get_or_raise(r1.id).title == "Updated Title"
    assert repo.get_or_raise(r1.id).year == 1875

    assert repo.delete(r2.id) is True
    assert repo.delete(r2.id) is False
    assert repo.count() == 2


def test_count_list_all_and_find_by(repo: DummyRecordRepository) -> None:
    """Verify count variations, list_all pagination/sorting, and find_by filtering."""
    repo.upsert_many(
        [
            _make_record(1, title="Alpha", year=1910),
            _make_record(2, title="Beta", year=1900),
            _make_record(3, title="Gamma", year=1910),
        ]
    )

    assert repo.count() == 3
    assert repo.count({"year": 1910}) == 2
    assert repo.count(repo.query().where("year", 1900)) == 1

    all_asc = repo.list_all()
    assert [r.id.value for r in all_asc] == [
        "SID-000001",
        "SID-000002",
        "SID-000003",
    ]

    paged = repo.list_all(
        limit=1,
        offset=1,
        order_by="year",
        sort_order=SortOrder.DESC,
    )
    assert len(paged) == 1
    assert paged[0].year == 1910

    matched = repo.find_by(year=1910)
    assert len(matched) == 2
    assert [m.id.value for m in matched] == ["SID-000001", "SID-000003"]


def test_repository_error_translation(
    repo: DummyRecordRepository,
    tmp_path: Path,
) -> None:
    """Verify DatabaseError and EntityMappingError translate into RepositoryError."""
    bad_entity = _make_record(99, title="FAIL_TO_ROW")
    with pytest.raises(RepositoryError, match="Failed to insert record"):
        repo.insert(bad_entity)

    with pytest.raises(RepositoryError, match="Batch upsert failed"):
        repo.upsert_many([bad_entity])

    poison_row = _make_record(98, title="FAIL_FROM_ROW")
    repo.upsert(poison_row)
    with pytest.raises(RepositoryError, match="Query execution failed"):
        repo.get(poison_row.id)

    uninitialized_session = DatabaseSessionManager(db_path=tmp_path / "missing_schema.db")
    broken_repo = DummyRecordRepository(
        mapper=DummyRecordMapper(),
        session_manager=uninitialized_session,
    )

    with pytest.raises(RepositoryError, match="Failed to count records"):
        broken_repo.count()

    with pytest.raises(RepositoryError, match="Failed to delete record"):
        broken_repo.delete("SID-000001")


def test_count_handles_empty_fetchone_gracefully(
    repo: DummyRecordRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify count() returns 0 if cursor.fetchone() returns None."""

    class _FakeCursor:
        def fetchone(self) -> None:
            return None

    class _FakeConn:
        def __enter__(self) -> _FakeConn:
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def execute(self, sql: str, params: object = None) -> _FakeCursor:
            return _FakeCursor()

    monkeypatch.setattr(repo.session_manager, "get_connection", lambda: _FakeConn())
    assert repo.count() == 0
