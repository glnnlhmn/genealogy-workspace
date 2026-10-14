# Name: conftest.py
# Path: tests/test_cli/conftest.py
# Version: 1.0.0+build.r1
"""Fixtures for CLI tests."""

import pytest


@pytest.fixture
def cli_runner_context():
    """Context state for CLI test dispatch."""
    return {"verbosity": 0, "dry_run": True}
