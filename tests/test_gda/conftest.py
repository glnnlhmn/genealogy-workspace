"""Path: tests/test_gda/conftest.py

Root pytest configuration and shared fixtures for the GDA test suite.

Operational Role:
    Provides universal, Tier-0-safe fixtures (environment isolation, fixed UTC
    strings/datetimes, canonical UUIDs, hermetic sandboxes, and Windows-safe
    logger teardown) at the top of the file, followed by separate Tier 2 and
    Tier 5 compatibility sections using lazy imports so Tier 0 test collection
    remains strictly isolated from higher tiers.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from gda.core.config import LoggingConfig
    from gda.core.logging import GDALogger
    from gda.model.atom.date import IsoTimestamp
    from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.4"

__all__ = [
    "clean_gda_env",
    "fixed_utc_datetime",
    "fixed_utc_iso_str",
    "fixed_utc_timestamp",
    "gda_sandbox_dir",
    "managed_gda_logger",
    "mock_db_session",
    "sample_uuid_v4",
    "valid_audit",
]


# ==============================================================================
# SECTION 1: TIER 0 GLOBAL ISOLATION & DETERMINISTIC PRIMITIVES
# Note: Pure stdlib / gda.core safe fixtures shared across all GDA tiers.
# ==============================================================================


@pytest.fixture(autouse=True)
def clean_gda_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip host GDA_* environment variables before each test for hermetic runs."""
    # Prevents workstation shell variables from leaking into AppConfig.load() (RARE-CORE-02).
    for key in list(os.environ):
        if key.startswith("GDA_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture(scope="session")
def fixed_utc_iso_str() -> str:
    """Provide a deterministic UTC ISO-8601 string with zero higher-tier dependencies."""
    return "2026-11-15T12:00:00Z"


@pytest.fixture(scope="session")
def fixed_utc_datetime() -> datetime:
    """Provide a deterministic timezone-aware UTC datetime matching fixed_utc_iso_str."""
    return datetime(2026, 11, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="session")
def sample_uuid_v4() -> str:
    """Provide a canonical lowercase RFC 4122 UUIDv4 string for cross-tier reuse."""
    return "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d"


@pytest.fixture
def gda_sandbox_dir(tmp_path: Path) -> Path:
    """Provision a standard hermetic GDA directory tree under tmp_path."""
    for rel in ("data", "runtime", "backups", "logs"):
        (tmp_path / rel).mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def managed_gda_logger(
    gda_sandbox_dir: Path,
) -> Generator[Callable[[str, LoggingConfig | None], GDALogger]]:
    """Yield a GDALogger factory that closes all file handlers on teardown.

    Explicitly closing handlers prevents Windows WinError 32 file-locking
    collisions when pytest cleans up tmp_path directories.
    """
    from gda.core.config import LoggingConfig
    from gda.core.logging import GDALogger

    created: list[GDALogger] = []

    def _make(name: str = "gda.test", config: LoggingConfig | None = None) -> GDALogger:
        cfg = config or LoggingConfig(
            level="DEBUG",
            log_to_console=False,
            log_to_file=False,
        )
        logger = GDALogger(name=name, config=cfg, base_dir=gda_sandbox_dir)
        created.append(logger)
        return logger

    yield _make

    for gda_logger in created:
        py_logger = getattr(gda_logger, "_logger", None)
        if py_logger is not None:
            for handler in list(py_logger.handlers):
                handler.close()
                py_logger.removeHandler(handler)


# ==============================================================================
# SECTION 2: TIER 2 COMPATIBILITY FIXTURES (MODEL / AUDIT)
# Note: Lazy-imported to preserve Tier 0 collection isolation while keeping all
# downstream model, entity, and repository suites working unchanged.
# ==============================================================================


@pytest.fixture
def fixed_utc_timestamp(fixed_utc_iso_str: str) -> IsoTimestamp:
    """Provide a deterministic UTC IsoTimestamp for model, entity, and db tests."""
    from gda.model.atom.date import IsoTimestamp

    return IsoTimestamp(fixed_utc_iso_str)


@pytest.fixture
def valid_audit(fixed_utc_timestamp: IsoTimestamp) -> AuditStamp:
    """Provide a canonical AuditStamp anchored to fixed_utc_timestamp."""
    from gda.model.base.audit import AuditStamp

    return AuditStamp(created_at=fixed_utc_timestamp, updated_at=fixed_utc_timestamp)


# ==============================================================================
# SECTION 3: TIER 5 COMPATIBILITY FIXTURES (DATABASE / SESSION)
# Note: Mock session double for database and repository unit tests.
# ==============================================================================


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
