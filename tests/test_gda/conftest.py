# Name: conftest.py
# Path: tests/test_gda/conftest.py
# Version: 1.0.0+build.r1
"""Fixtures for gda core library testing."""

import pytest


@pytest.fixture
def mock_gda_env(monkeypatch, tmp_path):
    """Hermetic environment routing for gda tests."""
    monkeypatch.setenv("GDA_ROOT", str(tmp_path))
    return tmp_path
