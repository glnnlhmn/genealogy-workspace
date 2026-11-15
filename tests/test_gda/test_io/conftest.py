"""Path: tests/test_gda/test_io/conftest.py

Shared pytest fixtures for the gda.io persistence and Safe Backup verification suite.

Operational Role:
    Provides hermetic temporary file paths, sample UTF-8 text and JSON payloads,
    and isolated backup directory fixtures for gda.io unit and integration tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

__version__ = "1.0.0+build.1"


@pytest.fixture
def sample_json_payload() -> dict[str, Any]:
    """Provide a deterministic dictionary payload with Unicode characters for JSON I/O tests."""
    return {
        "a_key": 1,
        "name": "Müller",
        "z_key": "Grüße",
    }


@pytest.fixture
def sample_text_content() -> str:
    """Provide a canonical UTF-8 multiline markdown string for text I/O tests."""
    return "# Genealogy Note\nMüller lineage record, £100, 1850."


@pytest.fixture
def custom_backup_dir(tmp_path: Path) -> Path:
    """Provide an isolated custom backup directory inside the pytest tmp_path sandbox."""
    return tmp_path / "custom_backups"
