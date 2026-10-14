# Name: conftest.py
# Path: tests/test_ancestry_desk/conftest.py
# Version: 1.0.0+build.r1
"""Fixtures for ancestry_desk UI tests."""

import pytest


@pytest.fixture
def mock_session_state():
    """Mock session state dictionary."""
    return {"user": "analyst", "active_project": "default"}
