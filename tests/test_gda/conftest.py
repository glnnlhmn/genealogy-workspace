"""Path: tests/test_gda/conftest.py

Root pytest configuration and shared fixtures for the GDA test suite.

Operational Role:
    Provides universal, deterministic fixtures (fixed UTC timestamps,
    canonical AuditStamp instances, and hermetic SQLite session mocks)
    shared across core, io, util, model, entity, db, and manager test suites.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gda.model.atom.date import IsoTimestamp
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.2"


@pytest.fixture
def fixed_utc_timestamp() -> IsoTimestamp:
    """Provide a deterministic UTC ISO-8601 timestamp for reproducible tests."""
    return IsoTimestamp("2026-11-15T12:00:00Z")


@pytest.fixture
def valid_audit(fixed_utc_timestamp: IsoTimestamp) -> AuditStamp:
    """Provide a canonical AuditStamp anchored to fixed_utc_timestamp."""
    return AuditStamp(created_at=fixed_utc_timestamp, updated_at=fixed_utc_timestamp)


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Provide a mocked DatabaseSessionManager with connection and transaction contexts."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []

    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_cursor

    mock_tx = MagicMock()

    mock_session = MagicMock()
    mock_session.get_connection.return_value.__enter__.return_value = mock_conn
    mock_session.transaction.return_value.__enter__.return_value = mock_tx
    return mock_session
