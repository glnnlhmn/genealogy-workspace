# Name: conftest.py
# Path: tests/conftest.py
# Version: 1.0.0+build.r1
"""Root pytest fixtures and Windows DACL redirection."""

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def workspace_root() -> Path:
    """Return repository root path."""
    return Path(__file__).resolve().parent.parent
