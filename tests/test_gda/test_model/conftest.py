"""Path: tests/test_gda/test_model/conftest.py

Shared fixtures for model testing suites.
"""

from __future__ import annotations

from typing import Any

import pytest

from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import SourceID

__version__ = "1.0.0+build.7"


@pytest.fixture(scope="session")
def advanced_timestamp() -> IsoTimestamp:
    return IsoTimestamp("2026-10-16T14:30:00Z")


@pytest.fixture(scope="session")
def golden_guid() -> str:
    return "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d"


@pytest.fixture(scope="session")
def golden_source_id() -> SourceID:
    return SourceID("a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d")


@pytest.fixture(scope="session")
def golden_source_uuid() -> str:
    return "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d"


@pytest.fixture(scope="session")
def golden_source_uuid_2() -> str:
    return "b2c3d4e5-f6a1-4b2c-9d3e-4f5a6b7c8d9e"


@pytest.fixture(scope="session")
def failure_note_payload_missing_keys() -> dict[str, Any]:
    return {"note_id": "NOT-000018"}


@pytest.fixture(scope="session")
def failure_note_blank_text() -> str:
    return "   "
