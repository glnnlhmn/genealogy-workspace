"""Path: tests/test_gda/test_repository/conftest.py

Shared pytest fixtures for the gda.repository verification suite.

Operational Role:
    Centralizes the initialized SQLite DatabaseSessionManager (seeded_session)
    with core foreign-key reference rows (locations, sites, organizations,
    individuals) and deterministic AuditStamp fixtures for all repository and
    collection test modules.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gda.db.schema import SchemaManager
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.1"


@pytest.fixture
def golden_audit() -> AuditStamp:
    """Return a deterministic AuditStamp fixture for repository tests."""
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


@pytest.fixture
def seeded_session(tmp_path: Path) -> DatabaseSessionManager:
    """Provision an initialized SQLite DB with core FK reference rows."""
    db_file = tmp_path / "repository_test.db"
    session = DatabaseSessionManager(db_path=db_file)
    SchemaManager(session_manager=session).init_db()

    with session.transaction() as tx:
        tx.execute(
            """
            INSERT INTO locations (
                id, canonical_urn, raw_name, canonical_name, category, created_at, updated_at
            ) VALUES
            ('LOC-000001', 'urn:gda:loc:us:pa:cumberland', 'Cumberland County', 'Cumberland County', 'COUNTY_EQUIVALENT', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'),
            ('LOC-000002', 'urn:gda:loc:us:pa:lancaster', 'Lancaster County', 'Lancaster County', 'COUNTY_EQUIVALENT', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
            """
        )
        tx.execute(
            """
            INSERT INTO sites (
                id, canonical_urn, raw_name, canonical_name, category,
                location_id, created_at, updated_at
            ) VALUES (
                'SID-000001', 'urn:gda:site:us:pa:cumberland:zion_s000001',
                'Zion Lutheran Cemetery', 'Zion Lutheran Cemetery', 'CEMETERY',
                'LOC-000001', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )
        tx.execute(
            """
            INSERT INTO organizations (
                id, canonical_urn, raw_name, canonical_name, category,
                location_id, meeting_site_id, created_at, updated_at
            ) VALUES (
                'ORG-000001', 'urn:gda:org:pa:zion_lutheran',
                'Zion Lutheran Church', 'Zion Lutheran Church', 'RELIGIOUS',
                'LOC-000001', 'SID-000001',
                '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )
        for idx, (given, sur, sex) in enumerate(
            [("John", "Lehman", "MALE"), ("Mary", "Miller", "FEMALE")],
            start=1,
        ):
            tx.execute(
                """
                INSERT INTO individuals (
                    id, canonical_urn, raw_name, canonical_name,
                    given_name, surname, gender, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
                """,
                (
                    f"IND-{idx:06d}",
                    f"urn:gda:ind:{idx:06d}",
                    f"{given} {sur}",
                    f"{given} {sur}",
                    given,
                    sur,
                    sex,
                ),
            )
    return session
